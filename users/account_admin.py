"""Administration des comptes dans RadGestMat, sans accès à Django admin."""
import logging
from functools import wraps
from urllib.parse import urlsplit

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.debug import sensitive_post_parameters

from assets.mail_transport import send_email
from assets.models import Departement
from .models import ProfilUtilisateur, UserPreferences

logger = logging.getLogger(__name__)


def can_administer_accounts(user):
    if not user.is_authenticated or not user.is_active:
        return False
    profile = getattr(user, 'profilutilisateur', None)
    return user.is_superuser or bool(
        profile and profile.actif and profile.role == 'SUPER_ADMIN'
    )


def accounts_required(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not can_administer_accounts(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def can_manage_target(actor, target):
    if actor.pk == target.pk:
        return False
    profile = getattr(target, 'profilutilisateur', None)
    if actor.is_superuser:
        return True
    return not (
        target.is_superuser or target.is_staff
        or (profile and profile.role == 'SUPER_ADMIN')
    )


def target_for_change(request, pk):
    target = get_object_or_404(User, pk=pk)
    if not can_manage_target(request.user, target):
        raise PermissionDenied
    return target


class AccountForm(forms.ModelForm):
    password = forms.CharField(
        label='Mot de passe initial', required=False, strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='Facultatif à la création avec une adresse email : envoyez ensuite un lien de réinitialisation.',
    )
    departement = forms.ModelChoiceField(
        label='Département', queryset=Departement.objects.all()
    )
    role = forms.ChoiceField(label='Rôle', choices=ProfilUtilisateur.ROLE_CHOICES)
    telephone = forms.CharField(label='Téléphone', required=False, max_length=20)
    date_embauche = forms.DateField(
        label="Date d’embauche", required=False,
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
    )
    dark_mode = forms.BooleanField(label='Mode sombre', required=False)
    is_active = forms.BooleanField(label='Compte actif', required=False, initial=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        if not actor.is_superuser:
            self.fields['role'].choices = [
                (key, label) for key, label in ProfilUtilisateur.ROLE_CHOICES
                if key != 'SUPER_ADMIN'
            ]
        if self.instance.pk:
            self.fields.pop('password')
            profile = getattr(self.instance, 'profilutilisateur', None)
            if profile:
                for field in ('departement', 'role', 'telephone', 'date_embauche'):
                    self.initial[field] = getattr(profile, field)
                self.initial['is_active'] = self.instance.is_active and profile.actif
            prefs = getattr(self.instance, 'preferences', None)
            self.initial['dark_mode'] = bool(prefs and prefs.dark_mode)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                css = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                css = 'form-select'
            else:
                css = 'form-control'
            field.widget.attrs['class'] = css

    def clean(self):
        data = super().clean()
        if not self.instance.pk and not data.get('password') and not data.get('email'):
            self.add_error('email', 'Une adresse email est nécessaire si aucun mot de passe initial ne sera défini.')
        return data

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get('password')
        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as exc:
                self.add_error('password', exc)

    @transaction.atomic
    def save(self):
        creating = not self.instance.pk
        target = super().save(commit=False)
        if creating:
            if self.cleaned_data.get('password'):
                target.set_password(self.cleaned_data['password'])
            else:
                target.set_unusable_password()
        target.save()
        ProfilUtilisateur.objects.update_or_create(
            user=target,
            defaults={
                'departement': self.cleaned_data['departement'],
                'role': self.cleaned_data['role'],
                'telephone': self.cleaned_data['telephone'],
                'date_embauche': self.cleaned_data['date_embauche'],
                'actif': target.is_active,
            },
        )
        UserPreferences.objects.update_or_create(
            user=target, defaults={'dark_mode': self.cleaned_data['dark_mode']}
        )
        return target


@accounts_required
def user_list(request):
    users = User.objects.select_related('profilutilisateur__departement').order_by('username')
    search = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '')
    dept_filter = request.GET.get('departement', '')
    status = request.GET.get('statut', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) | Q(email__icontains=search)
            | Q(first_name__icontains=search) | Q(last_name__icontains=search)
        )
    if role_filter in dict(ProfilUtilisateur.ROLE_CHOICES):
        users = users.filter(profilutilisateur__role=role_filter)
    if dept_filter.isdigit() and len(dept_filter) <= 10:
        users = users.filter(profilutilisateur__departement_id=int(dept_filter))
    if status == 'actif':
        users = users.filter(is_active=True).exclude(profilutilisateur__actif=False)
    elif status == 'inactif':
        users = users.filter(Q(is_active=False) | Q(profilutilisateur__actif=False))
    return render(request, 'users/user_list.html', {
        'users': users, 'search': search, 'role_filter': role_filter,
        'dept_filter': dept_filter, 'status': status,
        'departements': Departement.objects.order_by('nom'),
    })


@accounts_required
def user_detail(request, pk):
    target = get_object_or_404(User.objects.select_related('profilutilisateur__departement', 'preferences'), pk=pk)
    return render(request, 'users/user_detail.html', {
        'target': target, 'profil': getattr(target, 'profilutilisateur', None),
        'can_manage': can_manage_target(request.user, target),
    })


@accounts_required
@sensitive_post_parameters('password')
@require_http_methods(['GET', 'POST'])
def user_create(request):
    form = AccountForm(request.POST if request.method == 'POST' else None, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        target = form.save()
        messages.success(request, 'Compte créé. Vous pouvez envoyer un lien de réinitialisation depuis sa fiche.')
        return redirect('users:user_detail', pk=target.pk)
    return render(request, 'users/user_form.html', {'form': form})


@accounts_required
@sensitive_post_parameters('password')
@require_http_methods(['GET', 'POST'])
def user_update(request, pk):
    target = target_for_change(request, pk)
    form = AccountForm(request.POST if request.method == 'POST' else None, instance=target, actor=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Compte et préférences mis à jour.')
        return redirect('users:user_detail', pk=target.pk)
    return render(request, 'users/user_form.html', {'form': form, 'target': target})


@accounts_required
@require_http_methods(['GET', 'POST'])
def user_delete(request, pk):
    """Ancienne route de suppression : désactivation sans perte d'historique."""
    target = target_for_change(request, pk)
    if request.method == 'POST':
        with transaction.atomic():
            target.is_active = False
            target.save(update_fields=['is_active'])
            ProfilUtilisateur.objects.filter(user=target).update(actif=False)
        messages.success(request, 'Compte désactivé. Son historique est conservé.')
        return redirect('users:user_detail', pk=target.pk)
    return render(request, 'users/user_confirm_delete.html', {'target': target})


@accounts_required
@sensitive_post_parameters('new_password1', 'new_password2')
@require_http_methods(['GET', 'POST'])
def user_password(request, pk):
    target = target_for_change(request, pk)
    form = SetPasswordForm(target, request.POST if request.method == 'POST' else None)
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Mot de passe modifié. Les anciennes sessions et liens de réinitialisation sont invalidés.')
        return redirect('users:user_detail', pk=target.pk)
    return render(request, 'users/admin_password.html', {'form': form, 'target': target})


def reset_eligible(target):
    profile = getattr(target, 'profilutilisateur', None)
    return target.is_active and (profile is None or profile.actif)


def reset_link(request, target):
    path = reverse('users:password_reset_confirm', kwargs={
        'uidb64': urlsafe_base64_encode(force_bytes(target.pk)),
        'token': default_token_generator.make_token(target),
    })
    site = (getattr(settings, 'SITE_URL', '') or '').strip().rstrip('/')
    if site:
        parts = urlsplit(site)
        if parts.scheme not in ('http', 'https') or not parts.netloc or parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError('SITE_URL invalide')
        if not settings.DEBUG and parts.scheme != 'https':
            raise ValueError('HTTPS obligatoire')
        return site + path
    if not settings.DEBUG and not request.is_secure():
        raise ValueError('HTTPS obligatoire')
    return request.build_absolute_uri(path)


@accounts_required
@require_POST
def user_send_reset(request, pk):
    target = target_for_change(request, pk)
    if not reset_eligible(target):
        messages.error(request, 'Réactivez le compte avant d’envoyer un lien.')
        return redirect('users:user_detail', pk=pk)
    try:
        validate_email(target.email)
    except ValidationError:
        messages.error(request, 'Renseignez une adresse email valide avant cet envoi.')
        return redirect('users:user_detail', pk=pk)
    try:
        link = reset_link(request, target)
        result = send_email(
            subject='[RadGestMat] Réinitialisation de votre mot de passe',
            message=(
                f'Bonjour {target.get_full_name() or target.username},\n\n'
                f'Un administrateur de RadGestMat vous invite à définir un nouveau mot de passe '
                f'pour votre compte {target.username}.\n\n{link}\n\n'
                'Ce lien est personnel et utilisable une seule fois après changement du mot de passe. '
                f'Il expire au bout de {settings.PASSWORD_RESET_TIMEOUT // 3600} heures. '
                'Si vous ne reconnaissez pas cette demande, contactez le support informatique.'
            ),
            recipient_list=[target.email],
        )
        if not result:
            raise RuntimeError('Aucun email accepté')
    except Exception:
        # Ne jamais journaliser le lien, le jeton ou les détails de transport.
        logger.warning('Echec envoi lien de réinitialisation pour compte id=%s', target.pk)
        messages.error(request, 'Envoi impossible. Vérifiez la configuration de messagerie ou réessayez.')
    else:
        messages.success(request, 'Lien de réinitialisation transmis au service de messagerie.')
    return redirect('users:user_detail', pk=pk)


class AccountResetConfirm(auth_views.PasswordResetConfirmView):
    template_name = 'users/reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')

    def get_user(self, uidb64):
        user = super().get_user(uidb64)
        if user is not None and reset_eligible(user):
            return user
        return None
