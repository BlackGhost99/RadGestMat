"""Mobile authentication using existing Django sessions and CSRF protection."""
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from users.models import ProfilUtilisateur


def account_scope(user):
    if not user.is_authenticated or not user.is_active:
        return None
    profile = ProfilUtilisateur.objects.filter(user=user).first()
    if profile and not profile.actif:
        return None
    if user.is_superuser or (profile and profile.role == "SUPER_ADMIN"):
        return {"account_id": user.pk, "role": "SUPER_ADMIN", "department_id": None}
    if profile and profile.role in ("DEPT_MANAGER", "DEPT_USER"):
        return {"account_id": user.pk, "role": profile.role, "department_id": profile.departement_id}
    return None


@never_cache
@require_GET
def session_status(request):
    scope = account_scope(request.user)
    response = {"csrf_token": get_token(request), "authenticated": scope is not None}
    if scope:
        response.update(scope)
        response["offline_until"] = timezone.now() + timedelta(hours=72)
    return JsonResponse(response)


@never_cache
@require_POST
@csrf_protect
def sign_in(request):
    username = request.POST.get("username", "")
    password = request.POST.get("password", "")
    if len(username) > 150 or len(password) > 4096:
        return JsonResponse({"error": "invalid_credentials"}, status=401)
    user = authenticate(request, username=username, password=password)
    scope = account_scope(user) if user is not None else None
    if scope is None:
        return JsonResponse({"error": "invalid_credentials"}, status=401)
    login(request, user)
    return JsonResponse({**scope, "csrf_token": get_token(request),
                         "offline_until": timezone.now() + timedelta(hours=72)})


@never_cache
@require_POST
@csrf_protect
def sign_out(request):
    logout(request)
    return JsonResponse({"authenticated": False})
