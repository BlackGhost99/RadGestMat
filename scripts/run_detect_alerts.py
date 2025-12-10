import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'radgestmat.settings')
django.setup()

from assets.services import AlerteService

res = AlerteService.detecter_toutes_alertes()

summary = {
    'total': res.get('total'),
    'counts': {k: len(v) if isinstance(v, list) else 0 for k, v in res.items()}
}
print(json.dumps(summary, indent=2, default=str))

# Print brief details for each category
for k, v in res.items():
    if isinstance(v, list) and v:
        print('\n--- {} ({} created) ---'.format(k, len(v)))
        for a in v[:10]:
            print(f"id={a.pk} type={a.type_alerte} severite={a.severite} desc={str(a.description)[:200]}")
