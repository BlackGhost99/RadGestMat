# assets/email_service.py
"""
Service d'envoi d'emails pour les alertes et les notifications.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from users.models import ProfilUtilisateur

from .models import Alerte, NotificationLog

logger = logging.getLogger(__name__)


class EmailAlerteService:
    """Service pour envoyer des emails concernant les alertes."""

    @staticmethod
    def envoyer_alerte_critique(alerte):
        """Envoie un email pour une alerte critique."""
        if alerte.severite != Alerte.SEVERITE_CRITICAL:
            return False

        managers = ProfilUtilisateur.objects.filter(
            departement=alerte.departement,
            role__in=['SUPER_ADMIN', 'DEPT_MANAGER'],
            actif=True,
        ).select_related('user')

        if not managers.exists():
            return False

        subject = f"[RadGestMat] Alerte Critique: {alerte.get_type_alerte_display()}"
        context = {
            'alerte': alerte,
            'site_name': 'RadGestMat',
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }

        html_message = render_to_string('assets/emails/alerte_critique.html', context)
        plain_message = strip_tags(html_message)
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
        except Exception as exc:
            logger.error("Erreur lors de l'envoi de l'email d'alerte: %s", exc, exc_info=True)
            return False

    @staticmethod
    def envoyer_rapport_quotidien(departement=None):
        """Envoie un rapport quotidien des alertes aux managers."""
        from .services import AlerteService

        if departement:
            managers = ProfilUtilisateur.objects.filter(
                departement=departement,
                role__in=['SUPER_ADMIN', 'DEPT_MANAGER'],
                actif=True,
            ).select_related('user')
        else:
            managers = ProfilUtilisateur.objects.filter(
                role='SUPER_ADMIN',
                actif=True,
            ).select_related('user')

        if not managers.exists():
            return False

        if departement:
            alertes = AlerteService.get_alertes_non_reglementees(departement)
        else:
            alertes = AlerteService.get_alertes_non_reglementees()

        stats = {
            'total': alertes.count(),
            'critique': alertes.filter(severite=Alerte.SEVERITE_CRITICAL).count(),
            'warning': alertes.filter(severite=Alerte.SEVERITE_WARNING).count(),
            'retard': alertes.filter(type_alerte=Alerte.TYPE_RETARD).count(),
            'defectueux': alertes.filter(type_alerte=Alerte.TYPE_DEFECTUEUX).count(),
            'stock_critique': alertes.filter(type_alerte=Alerte.TYPE_STOCK_CRITIQUE).count(),
            'perdu': alertes.filter(type_alerte=Alerte.TYPE_PERDU).count(),
        }

        subject = "[RadGestMat] Rapport Quotidien des Alertes"
        if departement:
            subject += f" - {departement.nom}"

        context = {
            'alertes': alertes[:10],
            'stats': stats,
            'departement': departement,
            'site_name': 'RadGestMat',
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }

        html_message = render_to_string('assets/emails/rapport_quotidien.html', context)
        plain_message = strip_tags(html_message)
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
        except Exception as exc:
            logger.error("Erreur lors de l'envoi du rapport quotidien: %s", exc, exc_info=True)
            return False


class NotificationEmailService:
    """Service pour envoyer les notifications de materiel par email."""

    ROLE_RECEVEUR = 'RECEVEUR'
    ROLE_PRETEUR = 'PRETEUR'

    @staticmethod
    def send_notification(notification_log, recipient_role=None):
        """
        Envoyer une notification par email.

        Args:
            notification_log: Instance de NotificationLog
            recipient_role: "RECEVEUR" ou "PRETEUR" pour personnaliser le contenu

        Returns:
            bool: True si envoye avec succes
        """
        try:
            subject = NotificationEmailService._get_subject(
                notification_log,
                recipient_role=recipient_role,
            )
            html_message = NotificationEmailService._get_html_message(
                notification_log,
                recipient_role=recipient_role,
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification_log.destinataire],
                html_message=html_message,
                fail_silently=False,
            )

            notification_log.statut = NotificationLog.STATUT_ENVOYEE
            notification_log.save(update_fields=['statut'])

            logger.info(
                "Email notification %s envoye a %s",
                notification_log.id,
                notification_log.destinataire,
            )
            return True

        except Exception as exc:
            logger.error(
                "Erreur lors de l'envoi notification %s: %s",
                notification_log.id,
                exc,
                exc_info=True,
            )
            notification_log.statut = NotificationLog.STATUT_ECHEC
            notification_log.erreur_message = str(exc)
            notification_log.save(update_fields=['statut', 'erreur_message'])
            return False

    @staticmethod
    def _resolve_recipient_role(notification_log, recipient_role=None):
        if recipient_role:
            return recipient_role

        if notification_log.type_notification != NotificationLog.TYPE_CREATION:
            return None

        attribution = notification_log.attribution
        recipient_email = (notification_log.destinataire or '').strip().lower()
        lender_email = (
            getattr(getattr(attribution, 'employe_responsable', None), 'email', '') or ''
        ).strip().lower()

        if recipient_email and lender_email and recipient_email == lender_email:
            return NotificationEmailService.ROLE_PRETEUR

        return NotificationEmailService.ROLE_RECEVEUR

    @staticmethod
    def _get_subject(notification_log, recipient_role=None):
        """Generer le sujet du mail selon type + role destinataire."""
        resolved_role = NotificationEmailService._resolve_recipient_role(
            notification_log,
            recipient_role=recipient_role,
        )

        if notification_log.type_notification == NotificationLog.TYPE_CREATION:
            if resolved_role == NotificationEmailService.ROLE_PRETEUR:
                label = "Nouvelle attribution enregistree - Confirmation de pret"
            else:
                label = "Materiel emprunte - Confirmation"
            return f"[RadGestMat] {label}"

        type_map = {
            NotificationLog.TYPE_RAPPEL_2H: "Rappel: Retour du materiel dans 2h",
            NotificationLog.TYPE_RAPPEL_J_MOINS_2: "Rappel: 2 jours avant le retour",
            NotificationLog.TYPE_RAPPEL_J_MOINS_1: "Rappel: 1 jour avant le retour",
            NotificationLog.TYPE_RAPPEL_FINAL: "Dernier jour: Veuillez retourner le materiel",
            NotificationLog.TYPE_RETARD: "URGENT: Materiel non retourne",
            NotificationLog.TYPE_RESTITUTION: "Merci pour la restitution du materiel",
        }
        return f"[RadGestMat] {type_map.get(notification_log.type_notification, 'Notification')}"

    @staticmethod
    def _get_html_message(notification_log, recipient_role=None):
        """Generer le HTML du mail selon type + role destinataire."""
        attribution = notification_log.attribution
        resolved_role = NotificationEmailService._resolve_recipient_role(
            notification_log,
            recipient_role=recipient_role,
        )

        context = {
            'attribution': attribution,
            'materiel': attribution.materiel,
            'client': attribution.client,
            'notification_type': notification_log.type_notification,
            'duree_emprunt': attribution.get_duree_emprunt_display(),
            'recipient_role': resolved_role,
            'site_name': 'RadGestMat',
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }

        if notification_log.type_notification == NotificationLog.TYPE_CREATION:
            if resolved_role == NotificationEmailService.ROLE_PRETEUR:
                template = 'assets/emails/notification_creation_preteur.html'
            else:
                template = 'assets/emails/notification_creation.html'
            return render_to_string(template, context)

        template_map = {
            NotificationLog.TYPE_RAPPEL_2H: 'assets/emails/notification_rappel_2h.html',
            NotificationLog.TYPE_RAPPEL_J_MOINS_2: 'assets/emails/notification_rappel_j2.html',
            NotificationLog.TYPE_RAPPEL_J_MOINS_1: 'assets/emails/notification_rappel_j1.html',
            NotificationLog.TYPE_RAPPEL_FINAL: 'assets/emails/notification_rappel_final.html',
            NotificationLog.TYPE_RETARD: 'assets/emails/notification_retard.html',
            NotificationLog.TYPE_RESTITUTION: 'assets/emails/notification_restitution.html',
        }

        template = template_map.get(
            notification_log.type_notification,
            'assets/emails/notification_base.html',
        )
        return render_to_string(template, context)

    @staticmethod
    def send_creation_notification(attribution, destinataire_email, type_client='CLIENT', recipient_role=None):
        """
        Envoyer notification de creation d'attribution.

        Args:
            attribution: Instance Attribution
            destinataire_email: Email du destinataire
            type_client: Compatibilite legacy (CLIENT ou USER)
            recipient_role: ROLE_RECEVEUR / ROLE_PRETEUR
        """
        notification_log = NotificationLog.objects.create(
            attribution=attribution,
            type_notification=NotificationLog.TYPE_CREATION,
            canal=NotificationLog.CANAL_EMAIL,
            duree_emprunt=attribution.duree_emprunt,
            destinataire=destinataire_email,
            statut=NotificationLog.STATUT_EN_ATTENTE,
        )

        if not recipient_role and type_client == 'USER':
            recipient_role = NotificationEmailService.ROLE_PRETEUR

        return NotificationEmailService.send_notification(
            notification_log,
            recipient_role=recipient_role,
        )

    @staticmethod
    def send_reminder_notification(attribution, type_rappel, destinataire_email):
        """Envoyer un rappel."""
        notification_log = NotificationLog.objects.create(
            attribution=attribution,
            type_notification=type_rappel,
            canal=NotificationLog.CANAL_EMAIL,
            duree_emprunt=attribution.duree_emprunt,
            destinataire=destinataire_email,
            statut=NotificationLog.STATUT_EN_ATTENTE,
        )

        return NotificationEmailService.send_notification(notification_log)

    @staticmethod
    def send_overdue_alert(attribution, destinataire_email, jours_retard=0):
        """Envoyer alerte retard."""
        notification_log = NotificationLog.objects.create(
            attribution=attribution,
            type_notification=NotificationLog.TYPE_RETARD,
            canal=NotificationLog.CANAL_EMAIL,
            duree_emprunt=attribution.duree_emprunt,
            destinataire=destinataire_email,
            statut=NotificationLog.STATUT_EN_ATTENTE,
        )

        return NotificationEmailService.send_notification(notification_log)

    @staticmethod
    def send_restitution_notification(attribution, destinataire_email):
        """Envoyer confirmation de restitution."""
        notification_log = NotificationLog.objects.create(
            attribution=attribution,
            type_notification=NotificationLog.TYPE_RESTITUTION,
            canal=NotificationLog.CANAL_EMAIL,
            duree_emprunt=attribution.duree_emprunt,
            destinataire=destinataire_email,
            statut=NotificationLog.STATUT_EN_ATTENTE,
        )

        return NotificationEmailService.send_notification(notification_log)
