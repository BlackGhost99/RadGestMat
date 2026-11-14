import json
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from assets.models import Materiel
from .mobile_auth import account_scope
from .mobile_operations import execute_once, OperationConflict


@never_cache
@require_POST
@csrf_protect
def update_material(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "authentication_required"}, status=401)
    try:
        if len(request.body) > 32768:
            return JsonResponse({"error": "payload_too_large"}, status=413)
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError()
        if set(payload) != {"operation_id", "material_id", "base_revision", "changes"}:
            raise ValueError()
        if type(payload["material_id"]) is not int:
            raise ValueError()
        changes = payload["changes"]
        allowed = {"nom": 200, "location": 200, "marque": 100, "modele": 100, "numero_serie": 100, "notes": 10000, "description": 10000}
        if not isinstance(changes, dict) or not changes or not set(changes) <= set(allowed):
            raise ValueError()
        for field, value in changes.items():
            if not isinstance(value, str) or len(value) > allowed[field] or (field == "nom" and not value.strip()):
                raise ValueError()
        revision = parse_datetime(payload["base_revision"])
        if revision is None or revision.tzinfo is None:
            raise ValueError()
        def authorize(user, data):
            scope = account_scope(user)
            if not scope or scope["role"] not in ("SUPER_ADMIN", "DEPT_MANAGER"):
                raise PermissionDenied()
            qs = Materiel.objects.filter(pk=data["material_id"])
            if scope["role"] != "SUPER_ADMIN":
                qs = qs.filter(departement_id=scope["department_id"])
            if not qs.exists():
                raise PermissionDenied()
        def mutate():
            scope = account_scope(request.user)
            qs = Materiel.objects.select_for_update().filter(pk=payload["material_id"])
            if not scope or scope["role"] not in ("SUPER_ADMIN", "DEPT_MANAGER"):
                raise PermissionDenied()
            if scope["role"] != "SUPER_ADMIN":
                qs = qs.filter(departement_id=scope["department_id"])
            material = qs.first()
            if material is None:
                raise PermissionDenied()
            # DjangoJSONEncoder truncates snapshot timestamps to milliseconds.
            current = material.date_modification
            current = current.replace(microsecond=current.microsecond // 1000 * 1000)
            if current != revision:
                raise OperationConflict("revision_conflict")
            for field, value in changes.items():
                setattr(material, field, value)
            material.full_clean()
            material.save(update_fields=[*changes, "date_modification"])
            return {"id": material.pk, "date_modification": material.date_modification.isoformat(timespec="milliseconds"), "changes": changes}
        result = execute_once(user=request.user, operation_id=payload["operation_id"], payload=payload, authorize=authorize, mutate=mutate)
        return JsonResponse(result)
    except PermissionDenied:
        return JsonResponse({"error": "access_denied"}, status=403)
    except OperationConflict:
        return JsonResponse({"error": "conflict"}, status=409)
    except (ValueError, TypeError, KeyError, AttributeError, ValidationError):
        return JsonResponse({"error": "invalid_operation"}, status=400)
