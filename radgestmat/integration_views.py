import os
import re
import secrets
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache

@require_GET
def android_assetlinks(request):
    fingerprints = [s.strip().upper() for s in os.environ.get("ANDROID_CERT_SHA256", "").split(",")]
    fingerprints = [s for s in fingerprints if re.fullmatch(r"(?:[0-9A-F]{2}:){31}[0-9A-F]{2}", s)]
    if not fingerprints:
        return JsonResponse([], safe=False, status=503)
    return JsonResponse([{"relation": ["delegate_permission/common.handle_all_urls"],
        "target": {"namespace": "android_app", "package_name": "com.radgestmat.app",
                   "sha256_cert_fingerprints": fingerprints}}], safe=False)

@csrf_exempt
@require_POST
@never_cache
def reminder_tick(request):
    expected = os.environ.get("REMINDER_JOB_TOKEN", "")
    supplied = request.headers.get("Authorization", "")
    if not expected or not secrets.compare_digest(supplied.encode(), ("Bearer " + expected).encode()):
        return JsonResponse({"error": "unauthorized"}, status=403)
    from assets import scheduler_jobs as jobs
    for job in (jobs.check_court_terme_reminders, jobs.check_moyen_terme_reminders,
                jobs.check_long_terme_reminders, jobs.check_overdue_materials):
        job()
    return JsonResponse({"jobs_invoked": 4})
