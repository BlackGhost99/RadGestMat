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

groups_data = [
    {
        'nom': 'IT',
        'code': 'IT',
        'desc': 'Département Technologies de l\'Information'
    },
    {
        'nom': 'SERVICE TECHNIQUE',
        'code': 'TECH',
        'desc': 'Services Techniques et Maintenance'
    },
    {
        'nom': 'BANQUET',
        'code': 'BANQ',
        'desc': 'Service Banquets et Événements'
    }
]

for g in groups_data:
    # 1. Créer le département
    dept, created = Departement.objects.get_or_create(
        code=g['code'],
        defaults={'nom': g['nom'], 'description': g['desc']}
    )
    action = "créé" if created else "existant"
    print(f"📍 Département {g['nom']} ({g['code']}) {action}")

    # 2. Créer un Manager pour ce département
    mgr_username = f"manager_{g['code'].lower()}"
    mgr_email = f"{mgr_username}@example.com"
    if not User.objects.filter(username=mgr_username).exists():
        u = User.objects.create_user(mgr_username, mgr_email, 'password123')
        ProfilUtilisateur.objects.create(
            user=u,
            departement=dept,
            role='DEPT_MANAGER'
        )
        print(f"   👤 Manager créé : {mgr_username} / password123")
    else:
        print(f"   👤 Manager existe déjà : {mgr_username}")

    # 3. Créer un User standard pour ce département
    usr_username = f"user_{g['code'].lower()}"
    usr_email = f"{usr_username}@example.com"
    if not User.objects.filter(username=usr_username).exists():
        u = User.objects.create_user(usr_username, usr_email, 'password123')
        ProfilUtilisateur.objects.create(
            user=u,
            departement=dept,
            role='DEPT_USER'
        )
        print(f"   👤 User créé : {usr_username} / password123")
    else:
        print(f"   👤 User existe déjà : {usr_username}")

print("\n✅ Initialisation terminée !")
