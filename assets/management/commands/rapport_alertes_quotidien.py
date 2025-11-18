# assets/management/commands/rapport_alertes_quotidien.py
"""
Commande de gestion pour envoyer les rapports quotidiens des alertes aux managers
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from assets.email_service import EmailAlerteService
from assets.models import Departement
from users.models import ProfilUtilisateur


class Command(BaseCommand):
    help = 'Envoie les rapports quotidiens des alertes aux managers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--departement',
            type=str,
            help='ID ou code du département (optionnel, par défaut tous les départements)',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Mode test: affiche les emails qui seraient envoyés sans les envoyer',
        )

    def handle(self, *args, **options):
        departement_id = options.get('departement')
        test_mode = options.get('test', False)
        
        self.stdout.write(self.style.SUCCESS('Démarrage de la génération des rapports quotidiens...'))
        
        if departement_id:
            try:
                # Essayer de trouver par ID ou code
                try:
                    departement = Departement.objects.get(id=int(departement_id))
                except (ValueError, Departement.DoesNotExist):
                    departement = Departement.objects.get(code=departement_id)
                
                self.stdout.write(f'Génération du rapport pour le département: {departement.nom}')
                
                if test_mode:
                    self.stdout.write(self.style.WARNING('Mode test: aucun email ne sera envoyé'))
                    # Afficher les managers qui recevraient l'email
                    managers = ProfilUtilisateur.objects.filter(
                        departement=departement,
                        role__in=['SUPER_ADMIN', 'DEPT_MANAGER'],
                        actif=True
                    ).select_related('user')
                    
                    self.stdout.write(f'Managers qui recevraient l\'email:')
                    for manager in managers:
                        if manager.user.email:
                            self.stdout.write(f'  - {manager.user.email} ({manager.user.get_full_name() or manager.user.username})')
                else:
                    success = EmailAlerteService.envoyer_rapport_quotidien(departement)
                    if success:
                        self.stdout.write(self.style.SUCCESS(f'✓ Rapport envoyé avec succès pour {departement.nom}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'✗ Erreur lors de l\'envoi du rapport pour {departement.nom}'))
                        
            except Departement.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Département non trouvé: {departement_id}'))
        else:
            # Envoyer à tous les départements
            departements = Departement.objects.all()
            
            if test_mode:
                self.stdout.write(self.style.WARNING('Mode test: aucun email ne sera envoyé'))
                self.stdout.write(f'Départements qui recevraient un rapport: {departements.count()}')
            else:
                for departement in departements:
                    self.stdout.write(f'Traitement du département: {departement.nom}')
                    success = EmailAlerteService.envoyer_rapport_quotidien(departement)
                    if success:
                        self.stdout.write(self.style.SUCCESS(f'✓ Rapport envoyé pour {departement.nom}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'⚠ Aucun manager trouvé pour {departement.nom}'))
        
        self.stdout.write(self.style.SUCCESS('Génération des rapports terminée.'))

