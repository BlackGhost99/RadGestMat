import os
import django
import sys

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "radgestmat.settings.production")
try:
    django.setup()
except Exception as e:
    os.environ["DJANGO_SETTINGS_MODULE"] = "radgestmat.settings.base"
    django.setup()

from django.contrib.auth.models import User
from users.models import ProfilUtilisateur

try:
    if not User.objects.filter(username='admin').exists():
        print("USER_MISSING")
        sys.exit(0)

    u = User.objects.get(username='admin')
    
    try:
        p = u.profilutilisateur
        print(f"Current Role: '{p.role}'")
        if p.role != 'SUPER_ADMIN':
            p.role = 'SUPER_ADMIN'
            p.save()
            print("ROLE_UPDATED_TO_SUPER_ADMIN")
        else:
            print("ROLE_ALREADY_SUPER_ADMIN")
            
    except Exception as e:
        print(f"PROFILE_MISSING_OR_ERROR: {e}")

except Exception as e:
    print(f"ERROR: {e}")
