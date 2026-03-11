import os
import django

# Force SQLite for local development
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "radgestmat.settings.base")
os.environ['DB_ENGINE'] = 'django.db.backends.sqlite3'
os.environ['DB_NAME'] = 'db.sqlite3'

django.setup()

from django.contrib.auth.models import User
from users.models import ProfilUtilisateur
from assets.models import Departement

# Create superuser if not exists
if not User.objects.filter(username='admin').exists():
    u = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("User 'admin' created with password 'admin'")
else:
    u = User.objects.get(username='admin')
    print("User 'admin' already exists")

# Create a default department
dept, created = Departement.objects.get_or_create(
    code='ADMIN',
    defaults={'nom': 'Administration', 'description': 'Département administratif'}
)
if created:
    print(f"Department '{dept.nom}' created")

# Create SUPER_ADMIN profile for admin user
if not hasattr(u, 'profilutilisateur') or u.profilutilisateur is None:
    try:
        p = ProfilUtilisateur.objects.create(
            user=u,
            departement=dept,
            role='SUPER_ADMIN'
        )
        print("Profile SUPER_ADMIN created for 'admin'")
    except Exception as e:
        print(f"Note: {e}")
else:
    p = u.profilutilisateur
    if p.role != 'SUPER_ADMIN':
        p.role = 'SUPER_ADMIN'
        p.save()
        print("Profile updated to SUPER_ADMIN")
    else:
        print("Profile already SUPER_ADMIN")

print("\n✅ Setup complete! Login with admin/admin")
