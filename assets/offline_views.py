"""Minimal read-only authenticated dataset for the Android client."""
import hashlib
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from .models import Materiel, Client, Categorie, Attribution, Alerte

@require_GET
@never_cache
def offline_snapshot(request):
    profile = getattr(request, "profil_utilisateur", None)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "authentication_required"}, status=401)
    if not profile or not profile.actif or not request.user.is_active or profile.role not in ("SUPER_ADMIN", "DEPT_MANAGER", "DEPT_USER"):
        return JsonResponse({"error": "forbidden"}, status=403)
    loans = Attribution.objects.select_related("materiel", "client", "salle").filter(date_retour_effective__isnull=True)
    if profile.role != "SUPER_ADMIN":
        if not profile.departement_id:
            return JsonResponse({"error": "department_required"}, status=403)
        loans = loans.filter(departement_id=profile.departement_id)
    materials = list(Materiel.objects.order_by("pk").values("id", "asset_id", "numero_inventaire", "nom", "marque", "modele", "statut_disponibilite", "etat_technique", "categorie__nom", "departement__nom", "location"))
    clients = list(Client.objects.order_by("pk").values("id", "nom", "type_client", "departement__nom"))
    categories = list(Categorie.objects.order_by("pk").values("id", "nom", "departement__nom"))
    alerts = list(Alerte.objects.filter(reglementee=False).order_by("pk").values("id", "type_alerte", "severite", "materiel__asset_id", "departement__nom"))
    active = []
    for loan in loans.order_by("pk"):
        active.append(dict(id=loan.pk, materiel_id=loan.materiel_id,
            asset_id=loan.materiel.asset_id, nom=loan.materiel.nom,
            destination=loan.client.nom if loan.client else (loan.salle.nom if loan.salle else ""),
            deadline=loan.retour_echeance(), personal=loan.employe_responsable_id == request.user.pk,
            type=loan.type_attribution))
    payload = dict(schema=1, user_id=request.user.pk, role=profile.role, department_id=profile.departement_id,
                   materials=materials, clients=clients, categories=categories, alerts=alerts, loans=active)
    raw = json.dumps(payload, cls=DjangoJSONEncoder, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > 8 * 1024 * 1024:
        return JsonResponse({"error": "snapshot_too_large"}, status=413)
    etag = '"' + hashlib.sha256(raw).hexdigest() + '"'
    response = HttpResponse(status=304) if request.headers.get("If-None-Match") == etag else HttpResponse(raw, content_type="application/json")
    response["ETag"] = etag
    return response
