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
    if not profil:
        return JsonResponse({"error": "profile_required"}, status=403)
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
