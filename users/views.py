from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
from .forms import UserForm, ProfilUtilisateurForm
from .models import UserPreferences

# Create your views here.
def index(request):
    """Simple placeholder view for the users app."""
    return HttpResponse('Users app: index')


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Logout user and redirect to logout confirmation page."""
    logout(request)
    return render(request, 'users/logout.html')


@login_required
@permission_required('auth.view_user', raise_exception=True)
def user_list(request):
    """Liste des utilisateurs avec filtrage."""
    from assets.models import Departement
    
    users = User.objects.all().select_related('profilutilisateur')
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    dept_filter = request.GET.get('departement', '')
    
    if search:
        users = users.filter(
            username__icontains=search
        ) | users.filter(
            email__icontains=search
        ) | users.filter(
            first_name__icontains=search
        )
    
    if role_filter:
        users = users.filter(profilutilisateur__role=role_filter)
    
    if dept_filter:
        users = users.filter(profilutilisateur__departement_id=dept_filter)
    
    departements = Departement.objects.all().order_by('nom')
    
    return render(request, 'users/user_list.html', {
        'users': users,
        'search': search,
        'role_filter': role_filter,
        'dept_filter': dept_filter,
        'departements': departements
    })


@login_required
@permission_required('auth.view_user', raise_exception=True)
def user_detail(request, pk):
    """Détail d'un utilisateur."""
    user = get_object_or_404(User, pk=pk)
    profil = getattr(user, 'profilutilisateur', None)
    return render(request, 'users/user_detail.html', {
        'user': user,
        'profil': profil
    })


@login_required
@permission_required('auth.add_user', raise_exception=True)
def user_create(request):
    """Créer un nouvel utilisateur."""
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profil_form = ProfilUtilisateurForm(request.POST)
        if user_form.is_valid() and profil_form.is_valid():
            user = user_form.save()
            profil = profil_form.save(commit=False)
            profil.user = user
            profil.save()
            messages.success(request, f'Utilisateur "{user.username}" créé avec succès.')
            return redirect('users:user_detail', pk=user.pk)
    else:
        user_form = UserForm()
        profil_form = ProfilUtilisateurForm()
    
    return render(request, 'users/user_form.html', {
        'user_form': user_form,
        'profil_form': profil_form
    })


@login_required
@permission_required('auth.change_user', raise_exception=True)
def user_update(request, pk):
    """Modifier un utilisateur."""
    user = get_object_or_404(User, pk=pk)
    profil = getattr(user, 'profilutilisateur', None)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profil_form = ProfilUtilisateurForm(request.POST, instance=profil) if profil else ProfilUtilisateurForm(request.POST)
        if user_form.is_valid() and profil_form.is_valid():
            user_form.save()
            profil = profil_form.save(commit=False)
            profil.user = user
            profil.save()
            messages.success(request, f'Utilisateur "{user.username}" modifié avec succès.')
            return redirect('users:user_detail', pk=user.pk)
    else:
        user_form = UserForm(instance=user)
        profil_form = ProfilUtilisateurForm(instance=profil) if profil else ProfilUtilisateurForm()
    
    return render(request, 'users/user_form.html', {
        'user_form': user_form,
        'profil_form': profil_form,
        'user': user
    })


@login_required
@permission_required('auth.delete_user', raise_exception=True)
def user_delete(request, pk):
    """Supprimer un utilisateur."""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'Utilisateur "{username}" supprimé avec succès.')
        return redirect('users:user_list')
    
    return render(request, 'users/user_confirm_delete.html', {'user': user})


@login_required
@require_http_methods(["GET", "POST"])
def user_settings(request):
    preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        dark_mode_enabled = request.POST.get('dark_mode') == 'on'
        preferences.dark_mode = dark_mode_enabled
        preferences.save()
        request.session['theme'] = 'dark' if dark_mode_enabled else 'light'
        messages.success(request, "Vos préférences ont été enregistrées.")
        return redirect('users:user_settings')
    
    context = {
        'preferences': preferences,
    }
    return render(request, 'users/settings.html', context)


@login_required
@csrf_exempt  # Temporarily exempt for testing, should use proper CSRF handling in production AJAX
@require_http_methods(["POST"])
def toggle_dark_mode(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            dark_mode = data.get('dark_mode', False)
            
            preferences, created = UserPreferences.objects.get_or_create(user=request.user)
            preferences.dark_mode = dark_mode
            preferences.save()
            
            request.session['theme'] = 'dark' if dark_mode else 'light'
            
            return JsonResponse({'success': True, 'theme': request.session['theme']})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
