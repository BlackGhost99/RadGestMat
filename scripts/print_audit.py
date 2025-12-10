import logging
import os
import sys
import pathlib
import django

# Ensure project root is on sys.path so `radgestmat` package can be imported
project_root = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

logging.getLogger().setLevel(logging.WARNING)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'radgestmat.settings.development')
django.setup()

from assets.models import AuditLog
from assets.views import _format_changes_for_display

qs = AuditLog.objects.order_by('-timestamp')[:5]
if not qs:
    print('No AuditLog entries found.')
for r in qs:
    print('----')
    print(r.timestamp, getattr(r.user, 'username', None), r.get_action_display())
    lines = _format_changes_for_display(r)
    if not lines:
        print('(no formatted changes)')
    for line in lines:
        print(line)
