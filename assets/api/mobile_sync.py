"""Mobile v1 read-only bootstrap; no legacy CRUD routes exposed."""
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache
from django.utils import timezone
from assets.models import Materiel, Departement, Categorie, Salle
from users.models import ProfilUtilisateur


@never_cache
@require_GET
def bootstrap(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "authentication_required"}, status=401)
    user = get_user_model().objects.filter(pk=request.user.pk, is_active=True).first()
    if user is None:
        return JsonResponse({"error": "access_denied"}, status=403)
    profile = ProfilUtilisateur.objects.filter(user=user).first()
    if profile is not None and not profile.actif:
        return JsonResponse({"error": "access_denied"}, status=403)
    global_access = user.is_superuser or bool(profile and profile.role == "SUPER_ADMIN")
    if not global_access and (not profile or profile.role not in ("DEPT_MANAGER", "DEPT_USER")):
        return JsonResponse({"error": "access_denied"}, status=403)
    departments = Departement.objects.all()
    if not global_access:
        departments = departments.filter(pk=profile.departement_id)
    department_ids = list(departments.values_list("pk", flat=True))
    materials = Materiel.objects.filter(departement_id__in=department_ids)
    categories = Categorie.objects.filter(departement_id__in=department_ids)
    rooms = Salle.objects.filter(departement_id__in=department_ids)
    return JsonResponse({
        "schema_version": 1,
        "snapshot_type": "full",
        "generated_at": timezone.now(),
        "account_id": user.pk,
        "department_ids": department_ids,
        "departements": list(departments.order_by("pk").values("id", "nom", "code")),
        "categories": list(categories.order_by("pk").values("id", "nom", "departement_id")),
        "salles": list(rooms.order_by("pk").values("id", "nom", "code", "departement_id")),
        "materiels": list(materials.order_by("pk").values(
            "id", "asset_id", "numero_inventaire", "nom", "description",
            "categorie_id", "departement_id", "salle_id", "location",
            "marque", "modele", "numero_serie", "etat_technique",
            "statut_disponibilite", "date_achat", "prix", "notes",
            "date_modification",
        )),
    })
