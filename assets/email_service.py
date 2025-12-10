# assets/email_service.py
"""
Service d'envoi d'emails pour les alertes et les notifications
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import datetime
from .models import Alerte, NotificationLog, Attribution
from users.models import ProfilUtilisateur
import logging

logger = logging.getLogger(__name__)


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
        subject = "[RadGestMat] Rapport Quotidien des Alertes"
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


# ============================================================================
# SERVICE DE NOTIFICATIONS PAR EMAIL
# ============================================================================

class NotificationEmailService:
    """Service pour envoyer les notifications de matériel par email"""
    
    @staticmethod
    def send_notification(notification_log):
        """
        Envoyer une notification par email
        
        Args:
            notification_log: Instance de NotificationLog
            
        Returns:
            bool: True si envoyé avec succès
        """
        try:
            attribution = notification_log.attribution
            subject = NotificationEmailService._get_subject(notification_log)
            html_message = NotificationEmailService._get_html_message(notification_log)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification_log.destinataire],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Mettre à jour le log
            notification_log.statut = NotificationLog.STATUT_ENVOYEE
            notification_log.save(update_fields=['statut'])
            
            logger.info(f"Email notification {notification_log.id} envoyé à {notification_log.destinataire}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi notification {notification_log.id}: {e}")
            notification_log.statut = NotificationLog.STATUT_ECHEC
            notification_log.erreur_message = str(e)
            notification_log.save(update_fields=['statut', 'erreur_message'])
            return False
    
    @staticmethod
    def _get_subject(notification_log):
        """Générer le sujet du mail selon le type"""
        type_map = {
            NotificationLog.TYPE_CREATION: "✓ Matériel emprunté - Confirmation",
            NotificationLog.TYPE_RAPPEL_2H: "⏰ Rappel: Retour du matériel dans 2h",
            NotificationLog.TYPE_RAPPEL_J_MOINS_2: "📅 Rappel: 2 jours avant le retour",
            NotificationLog.TYPE_RAPPEL_J_MOINS_1: "📅 Rappel: 1 jour avant le retour",
            NotificationLog.TYPE_RAPPEL_FINAL: "📅 Dernier jour: Veuillez retourner le matériel",
            NotificationLog.TYPE_RETARD: "⚠️ URGENT: Matériel non retourné",
            NotificationLog.TYPE_RESTITUTION: "✓ Merci pour la restitution du matériel",
        }
        return f"[RadGestMat] {type_map.get(notification_log.type_notification, 'Notification')}"
    
    @staticmethod
    def _get_html_message(notification_log):
        """Générer le HTML du mail selon le type"""
        attribution = notification_log.attribution
        
        # Construire le contexte
        context = {
            'attribution': attribution,
            'materiel': attribution.materiel,
            'client': attribution.client,
            'notification_type': notification_log.type_notification,
            'duree_emprunt': attribution.get_duree_emprunt_display(),
            'site_name': 'RadGestMat',
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        # Sélectionner le template selon le type
        template_map = {
            NotificationLog.TYPE_CREATION: 'assets/emails/notification_creation.html',
            NotificationLog.TYPE_RAPPEL_2H: 'assets/emails/notification_rappel_2h.html',
            NotificationLog.TYPE_RAPPEL_J_MOINS_2: 'assets/emails/notification_rappel_j2.html',
            NotificationLog.TYPE_RAPPEL_J_MOINS_1: 'assets/emails/notification_rappel_j1.html',
            NotificationLog.TYPE_RAPPEL_FINAL: 'assets/emails/notification_rappel_final.html',
            NotificationLog.TYPE_RETARD: 'assets/emails/notification_retard.html',
            NotificationLog.TYPE_RESTITUTION: 'assets/emails/notification_restitution.html',
        }
        
        template = template_map.get(notification_log.type_notification, 'assets/emails/notification_base.html')
        html_message = render_to_string(template, context)
        
        return html_message
    
    @staticmethod
    def send_creation_notification(attribution, destinataire_email, type_client='CLIENT'):
        """
        Envoyer notification de création d'attribution
        
        Args:
            attribution: Instance Attribution
            destinataire_email: Email du destinataire
            type_client: 'CLIENT' ou 'USER' (manager)
        """
        notification_log = NotificationLog.objects.create(
            attribution=attribution,
            type_notification=NotificationLog.TYPE_CREATION,
            canal=NotificationLog.CANAL_EMAIL,
            duree_emprunt=attribution.duree_emprunt,
            destinataire=destinataire_email
        )
        
        return NotificationEmailService.send_notification(notification_log)
    
    @staticmethod
    def send_reminder_notification(attribution, type_rappel, destinataire_email):
        """
        Envoyer un rappel
        
        Args:
            attribution: Instance Attribution
            type_rappel: TYPE_RAPPEL_2H, TYPE_RAPPEL_J_MOINS_2, etc.
            destinataire_email: Email du destinataire
        """
        notification_log = NotificationLog.objects.create(
            attribution=attribution,
            type_notification=type_rappel,
            canal=NotificationLog.CANAL_EMAIL,
            duree_emprunt=attribution.duree_emprunt,
            destinataire=destinataire_email
        )
        
        return NotificationEmailService.send_notification(notification_log)
    
    @staticmethod
    def send_overdue_alert(attribution, destinataire_email, jours_retard=0):
        """
        Envoyer alerte retard
        
        Args:
            attribution: Instance Attribution
            destinataire_email: Email
            jours_retard: Nombre de jours de retard
        """
        notification_log = NotificationLog.objects.create(
            attribution=attribution,
            type_notification=NotificationLog.TYPE_RETARD,
            canal=NotificationLog.CANAL_EMAIL,
            duree_emprunt=attribution.duree_emprunt,
            destinataire=destinataire_email
        )
        
        return NotificationEmailService.send_notification(notification_log)
    
    @staticmethod
    def send_restitution_notification(attribution, destinataire_email):
        """
        Envoyer confirmation de restitution
        
        Args:
            attribution: Instance Attribution
            destinataire_email: Email
        """
        notification_log = NotificationLog.objects.create(
            attribution=attribution,
            type_notification=NotificationLog.TYPE_RESTITUTION,
            canal=NotificationLog.CANAL_EMAIL,
            duree_emprunt=attribution.duree_emprunt,
            destinataire=destinataire_email
        )
        
        return NotificationEmailService.send_notification(notification_log)

