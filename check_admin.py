import os
import django
import sys

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "radgestmat.settings.production")
try:
    django.setup()
except Exception as e:
    # Fallback if production settings fail or need base
    print(f"Prod settings failed: {e}")
    os.environ["DJANGO_SETTINGS_MODULE"] = "radgestmat.settings.base"
    django.setup()

from django.contrib.auth.models import User
from users.models import ProfilUtilisateur
from assets.models import Departement

try:
    if not User.objects.filter(username='admin').exists():
        print("USER_MISSING")
        sys.exit(0)

    u = User.objects.get(username='admin')
    print(f"User found: {u.username} (Superuser: {u.is_superuser})")
    
    try:
        p = u.profilutilisateur
        print("PROFILE_EXISTS")
        print(f"Role: {p.role}")
        print(f"Dept: {p.departement.nom}")
    except Exception as e:
        print("PROFILE_MISSING")
        # Auto-fix: Create profile if missing
        print("Attempting to create profile...")
        dept, _ = Departement.objects.get_or_create(code='DEF', defaults={'nom': 'Département par défaut'})
        ProfilUtilisateur.objects.create(
            user=u,
            departement=dept,
            role='SUPER_ADMIN'
        )
        print("PROFILE_CREATED")

except Exception as e:
    print(f"ERROR: {e}")
