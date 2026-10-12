"""
Crée le compte super administrateur au démarrage (utile sur Render, sans accès shell).

Utilise DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD et DJANGO_SUPERUSER_EMAIL.
Ne fait rien si ces variables sont absentes ou si le compte existe déjà :
le mot de passe n'est jamais écrasé.
"""
import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from assets.models import Departement
from users.models import ProfilUtilisateur


class Command(BaseCommand):
    help = "Crée le super administrateur à partir des variables d'environnement s'il n'existe pas"

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

        if not username or not password:
            self.stdout.write("ensure_admin : variables DJANGO_SUPERUSER_* absentes, rien à faire")
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"ensure_admin : '{username}' existe déjà")
            return

        user = User.objects.create_superuser(username, email, password)
        dept, _ = Departement.objects.get_or_create(
            code='ADMIN',
            defaults={'nom': 'Administration', 'description': 'Département administratif'},
        )
        ProfilUtilisateur.objects.create(user=user, departement=dept, role='SUPER_ADMIN')
        self.stdout.write(self.style.SUCCESS(f"ensure_admin : super administrateur '{username}' créé"))
