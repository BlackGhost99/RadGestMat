# assets/email_service.py
"""
Service d'envoi d'emails pour les alertes
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from .models import Alerte
from users.models import ProfilUtilisateur


class EmailAlerteService:
    """Service pour envoyer des emails concernant les alertes"""
    
    @staticmethod
    def envoyer_alerte_critique(alerte):
        """Envoie un email pour une alerte critique"""
        if not alerte.severite == Alerte.SEVERITE_CRITICAL:
            return False
        
        # Récupérer les managers du département concerné
        managers = ProfilUtilisateur.objects.filter(
            departement=alerte.departement,
            role__in=['SUPER_ADMIN', 'DEPT_MANAGER'],
            actif=True
        ).select_related('user')
        
        if not managers.exists():
            return False
        
        # Préparer le contenu de l'email
        subject = f"[RadGestMat] Alerte Critique: {alerte.get_type_alerte_display()}"
        
        context = {
            'alerte': alerte,
            'site_name': 'RadGestMat',
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        # Générer le contenu HTML
        html_message = render_to_string('assets/emails/alerte_critique.html', context)
        plain_message = strip_tags(html_message)
        
        # Envoyer à tous les managers
        emails = [profile.user.email for profile in managers if profile.user.email]
        
        if not emails:
            return False
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=emails,
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email d'alerte: {e}")
            return False
    
    @staticmethod
    def envoyer_rapport_quotidien(departement=None):
        """Envoie un rapport quotidien des alertes aux managers"""
        from .services import AlerteService
        
        # Récupérer les managers
        if departement:
            managers = ProfilUtilisateur.objects.filter(
                departement=departement,
                role__in=['SUPER_ADMIN', 'DEPT_MANAGER'],
                actif=True
            ).select_related('user')
        else:
            # Super admins seulement
            managers = ProfilUtilisateur.objects.filter(
                role='SUPER_ADMIN',
                actif=True
            ).select_related('user')
        
        if not managers.exists():
            return False
        
        # Récupérer les alertes
        if departement:
            alertes = AlerteService.get_alertes_non_reglementees(departement)
        else:
            alertes = AlerteService.get_alertes_non_reglementees()
        
        # Statistiques
        stats = {
            'total': alertes.count(),
            'critique': alertes.filter(severite=Alerte.SEVERITE_CRITICAL).count(),
            'warning': alertes.filter(severite=Alerte.SEVERITE_WARNING).count(),
            'retard': alertes.filter(type_alerte=Alerte.TYPE_RETARD).count(),
            'defectueux': alertes.filter(type_alerte=Alerte.TYPE_DEFECTUEUX).count(),
            'stock_critique': alertes.filter(type_alerte=Alerte.TYPE_STOCK_CRITIQUE).count(),
            'perdu': alertes.filter(type_alerte=Alerte.TYPE_PERDU).count(),
        }
        
        # Préparer le contenu
        subject = f"[RadGestMat] Rapport Quotidien des Alertes"
        if departement:
            subject += f" - {departement.nom}"
        
        context = {
            'alertes': alertes[:10],  # Top 10
            'stats': stats,
            'departement': departement,
            'site_name': 'RadGestMat',
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        # Générer le contenu HTML
        html_message = render_to_string('assets/emails/rapport_quotidien.html', context)
        plain_message = strip_tags(html_message)
        
        # Envoyer à tous les managers
        emails = [profile.user.email for profile in managers if profile.user.email]
        
        if not emails:
            return False
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=emails,
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi du rapport quotidien: {e}")
            return False

