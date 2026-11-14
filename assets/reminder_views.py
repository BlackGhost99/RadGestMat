from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache
from .models import Attribution


@require_GET
@never_cache
def personal_reminders(request):
    """Snapshot authoritative: only loans owned by the authenticated profile."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "authentication_required"}, status=401)
    profil = getattr(request, "profil_utilisateur", None)
    if not profil or not profil.actif:
        return JsonResponse({"error": "profile_required"}, status=403)
    if not _device_authorized(request):
        return JsonResponse({"error": "primary_device_required"}, status=403)
    qs = Attribution.objects.filter(
        employe_responsable=request.user,
        type_attribution=Attribution.TYPE_TEMPORAIRE,
        date_retour_effective__isnull=True,
        date_retour_prevue__isnull=False,
    ).select_related("materiel")
    if profil.role != "SUPER_ADMIN":
        if not profil.departement_id:
            return JsonResponse({"error": "department_required"}, status=403)
        qs = qs.filter(departement_id=profil.departement_id)
    reminders = []
    for loan in qs:
        deadline = loan.retour_echeance()
        reminders.append({
            "id": loan.pk,
            "asset_id": loan.materiel.asset_id,
            "deadline": deadline.isoformat(),
            "reminder_interval_minutes": 15,
        })
    return JsonResponse({
        "user_id": request.user.pk,
        "server_time": timezone.now().isoformat(),
        "reminders": reminders,
    })


from django.db import transaction
from django.views.decorators.http import require_POST
from users.models import ProfilUtilisateur
from .models import HistoriqueAttribution


@require_POST
@never_cache
@transaction.atomic
def transfer_reminder(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "authentication_required"}, status=401)
    profile = getattr(request, "profil_utilisateur", None)
    if not profile or not profile.actif or profile.role not in ("SUPER_ADMIN", "DEPT_MANAGER", "DEPT_USER"):
        return JsonResponse({"error": "forbidden"}, status=403)
    loans = Attribution.objects.select_for_update().filter(pk=pk)
    if profile.role != "SUPER_ADMIN":
        loans = loans.filter(departement_id=profile.departement_id)
    loan = loans.first()
    if not loan:
        return JsonResponse({"error": "not_found"}, status=404)
    if profile.role == "DEPT_USER" and loan.employe_responsable_id != request.user.pk:
        return JsonResponse({"error": "forbidden"}, status=403)
    if loan.date_retour_effective or not loan.retour_echeance():
        return JsonResponse({"error": "not_active"}, status=409)
    try:
        target_id = int(request.POST.get("user_id", ""))
    except (ValueError, TypeError):
        return JsonResponse({"error": "invalid_user"}, status=400)
    target = ProfilUtilisateur.objects.filter(
        user_id=target_id, departement_id=loan.departement_id,
        actif=True, user__is_active=True,
        role__in=("DEPT_USER", "DEPT_MANAGER", "SUPER_ADMIN"),
    ).select_related("user").first()
    if not target:
        return JsonResponse({"error": "invalid_target"}, status=400)
    previous = loan.employe_responsable_id
    if previous != target.user_id:
        loan.employe_responsable_id = target.user_id
        loan.save(update_fields=["employe_responsable"])
        HistoriqueAttribution.objects.create(
            attribution=loan, utilisateur=request.user,
            action=HistoriqueAttribution.ACTION_MODIFICATION,
            etat_avant=str(previous or ""),
            etat_apres=str(target.user_id),
            notes=f"Transfert de suivi : responsable {previous} vers {target.user_id}",
        )
    return JsonResponse({"id": loan.pk, "responsable_id": target.user_id})


# One revocable device credential per user.
import secrets
import hashlib
from django.utils.crypto import constant_time_compare
from .reminder_devices import ReminderDevice


def _digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _device_authorized(request):
    token = request.headers.get("X-Reminder-Device", "")
    if not token or len(token) > 256:
        return False
    device = ReminderDevice.objects.filter(user=request.user).first()
    return bool(device and constant_time_compare(device.token_hash, _digest(token)))


@require_POST
@never_cache
@transaction.atomic
def register_device(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "authentication_required"}, status=401)
    profile = getattr(request, "profil_utilisateur", None)
    if not profile or not profile.actif:
        return JsonResponse({"error": "forbidden"}, status=403)
    ProfilUtilisateur.objects.select_for_update().get(pk=profile.pk)
    token = secrets.token_urlsafe(48)
    ReminderDevice.objects.update_or_create(user=request.user, defaults={"token_hash": _digest(token)})
    return JsonResponse({"device_token": token, "user_id": request.user.pk})


@require_POST
@never_cache
@transaction.atomic
def revoke_device(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "authentication_required"}, status=401)
    token = request.headers.get("X-Reminder-Device", "")
    if token and len(token) <= 256:
        ReminderDevice.objects.filter(user=request.user, token_hash=_digest(token)).delete()
    return JsonResponse({"revoked": True})
