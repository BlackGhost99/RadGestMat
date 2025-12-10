from django.test import RequestFactory
from django.contrib.auth import get_user_model
from assets.models import AuditLog
from assets.views import report_pdf

User = get_user_model()
user = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_staff=True).first()
print('using user:', getattr(user, 'username', None))

if not user:
    print('No admin/staff user found; cannot run request.')
else:
    latest = AuditLog.objects.order_by('-pk').first()
    if not latest:
        print('No AuditLog entries found.')
    else:
        rf = RequestFactory()
        req = rf.get(f'/rapports/{latest.pk}/pdf/', SERVER_NAME='127.0.0.1', HTTP_HOST='127.0.0.1')
        req.user = user
        resp = report_pdf(req, pk=latest.pk)
        print('status_code=', getattr(resp, 'status_code', None))
        print('content_type=', resp.get('Content-Type'))
        content_len = len(getattr(resp, 'content', b''))
        print('len=', content_len)
        if resp.get('Content-Type') == 'application/pdf':
            print('PDF starts with:', resp.content[:12])
