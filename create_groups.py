import os
import django

# Force SQLite for local development
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "radgestmat.settings.base")
os.environ['DB_ENGINE'] = 'django.db.backends.sqlite3'
os.environ['DB_NAME'] = 'db.sqlite3'

django.setup()

from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from assets.models import Materiel, Attribution, Client

def setup_groups():
    groups_data = [
        {'name': 'IT', 'permissions': ['view_materiel', 'add_materiel', 'change_materiel', 'view_attribution', 'add_attribution', 'change_attribution', 'view_client']},
        {'name': 'SERVICE TECHNIQUE', 'permissions': ['view_materiel', 'add_materiel', 'change_materiel', 'view_attribution', 'add_attribution', 'change_attribution']},
        {'name': 'BANQUET', 'permissions': ['view_materiel', 'add_materiel', 'change_materiel', 'view_attribution', 'add_attribution', 'change_attribution', 'view_client']}
    ]

    for g_data in groups_data:
        group, created = Group.objects.get_or_create(name=g_data['name'])
        print(f"Groupe '{group.name}' {'créé' if created else 'existant'}")
        
        # Add permissions
        for perm_code in g_data['permissions']:
            try:
                perm = Permission.objects.get(codename=perm_code)
                group.permissions.add(perm)
                print(f"  + Permission ajoutée: {perm_code}")
            except Permission.DoesNotExist:
                print(f"  ! Permission introuvable: {perm_code}")

    # Add users to groups based on their username (simple mapping from previous script)
    # manager_it -> IT
    # user_it -> IT
    mapping = {
        'it': 'IT',
        'tech': 'SERVICE TECHNIQUE',
        'banq': 'BANQUET'
    }

    for suffix, group_name in mapping.items():
        try:
            group = Group.objects.get(name=group_name)
            
            # Find users matching pattern
            users = User.objects.filter(username__endswith=f"_{suffix}")
            for user in users:
                user.groups.add(group)
                print(f"  -> Utilisateur {user.username} ajouté au groupe {group.name}")
                
        except Group.DoesNotExist:
            print(f"Erreur: Groupe {group_name} introuvable")

if __name__ == '__main__':
    setup_groups()
    print("\n✅ Groupes et permissions configurés.")
