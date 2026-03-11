# assets/signals.py
"""
Signaux Django pour alertes et notifications d'attribution.
"""

import logging
import os
from types import SimpleNamespace

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .email_service import EmailAlerteService, NotificationEmailService
from .models import Alerte, Attribution, NotificationLog, NotificationPreferences
from .whatsapp_service import WhatsAppNotificationService

logger = logging.getLogger(__name__)

# Disable signals globally when requested by environment.
SIGNALS_DISABLED = os.environ.get("DISABLE_SIGNALS", "0") == "1"


def _default_preferences():
    return SimpleNamespace(
        notifications_email=True,
        notifications_whatsapp=False,
        phone_number=None,
    )


def _get_client_preferences(client):
    if not client:
        return _default_preferences()

    try:
        preferences, _ = NotificationPreferences.objects.get_or_create(client=client)
        return preferences
    except Exception as exc:
        logger.error(
            "Impossible de recuperer les preferences notifications du client %s: %s",
            client,
            exc,
            exc_info=True,
        )
        return _default_preferences()


def _send_email_notification(attribution, notification_type, recipient_email, recipient_role=None):
    if not recipient_email:
        return

    try:
        log = NotificationLog.objects.create(
            attribution=attribution,
            type_notification=notification_type,
            canal=NotificationLog.CANAL_EMAIL,
            duree_emprunt=attribution.duree_emprunt,
            destinataire=recipient_email,
            statut=NotificationLog.STATUT_EN_ATTENTE,
        )
        NotificationEmailService.send_notification(log, recipient_role=recipient_role)
    except Exception as exc:
        logger.error(
            "Erreur envoi email notification attribution=%s recipient=%s: %s",
            attribution.pk,
            recipient_email,
            exc,
            exc_info=True,
        )


def _send_whatsapp_notification(attribution, notification_type, phone_number):
    if not phone_number:
        return

    try:
        log = NotificationLog.objects.create(
            attribution=attribution,
            type_notification=notification_type,
            canal=NotificationLog.CANAL_WHATSAPP,
            duree_emprunt=attribution.duree_emprunt,
            destinataire=phone_number,
            statut=NotificationLog.STATUT_EN_ATTENTE,
        )
        WhatsAppNotificationService.send_notification(log)
    except Exception as exc:
        logger.error(
            "Erreur envoi WhatsApp attribution=%s recipient=%s: %s",
            attribution.pk,
            phone_number,
            exc,
            exc_info=True,
        )


# ============================================================================
# SIGNAUX POUR LES ALERTES CRITIQUES
# ============================================================================


@receiver(post_save, sender=Alerte)
def envoyer_email_alerte_critique(sender, instance, created, **kwargs):
    """Envoie un email automatiquement lorsqu'une alerte critique est creee."""
    if SIGNALS_DISABLED:
        return

    if created and instance.severite == Alerte.SEVERITE_CRITICAL:
        try:
            EmailAlerteService.envoyer_alerte_critique(instance)
        except Exception as exc:
            logger.error(
                "Erreur lors de l'envoi de l'email d'alerte: %s",
                exc,
                exc_info=True,
            )


# ============================================================================
# SIGNAUX POUR LES NOTIFICATIONS D'ATTRIBUTION
# ============================================================================


@receiver(pre_save, sender=Attribution)
def detecter_retour_materiel(sender, instance, **kwargs):
    """
    Detecte si le materiel vient d'etre retourne et marque l'instance.
    """
    if instance.pk:
        try:
            old_instance = Attribution.objects.get(pk=instance.pk)
            instance._notification_restitution_required = (
                not old_instance.date_retour_effective and bool(instance.date_retour_effective)
            )
        except Attribution.DoesNotExist:
            instance._notification_restitution_required = False
    else:
        instance._notification_restitution_required = False


@receiver(post_save, sender=Attribution)
def envoyer_notifications_attribution(sender, instance, created, **kwargs):
    """
    Envoi automatique des notifications:
    1) creation d'attribution
    2) restitution
    """
    if SIGNALS_DISABLED:
        return

    client_preferences = _get_client_preferences(instance.client)

    if created:
        logger.info("Nouvelle attribution creee: %s", instance.id)

        # Receveur du materiel (client)
        client_email = ""
        if instance.client:
            client_email = (instance.client.email or "").strip()

        if client_preferences.notifications_email and client_email:
            _send_email_notification(
                instance,
                NotificationLog.TYPE_CREATION,
                client_email,
                recipient_role="RECEVEUR",
            )
        elif instance.client and not client_email:
            logger.warning(
                "Aucun email client pour attribution=%s client=%s",
                instance.pk,
                instance.client_id,
            )

        # Employe qui prete le materiel (obligatoire metier)
        lender_email = (getattr(instance.employe_responsable, "email", "") or "").strip()
        if lender_email:
            _send_email_notification(
                instance,
                NotificationLog.TYPE_CREATION,
                lender_email,
                recipient_role="PRETEUR",
            )
        else:
            logger.error(
                "Email obligatoire manquant pour le preteur sur attribution=%s user=%s",
                instance.pk,
                instance.employe_responsable_id,
            )

        # WhatsApp creation (client uniquement, selon preferences)
        if client_preferences.notifications_whatsapp and client_preferences.phone_number:
            _send_whatsapp_notification(
                instance,
                NotificationLog.TYPE_CREATION,
                client_preferences.phone_number,
            )

    elif getattr(instance, "_notification_restitution_required", False):
        logger.info("Materiel retourne pour attribution=%s", instance.id)

        client_email = ""
        if instance.client:
            client_email = (instance.client.email or "").strip()

        if client_preferences.notifications_email and client_email:
            _send_email_notification(
                instance,
                NotificationLog.TYPE_RESTITUTION,
                client_email,
            )

        if client_preferences.notifications_whatsapp and client_preferences.phone_number:
            _send_whatsapp_notification(
                instance,
                NotificationLog.TYPE_RESTITUTION,
                client_preferences.phone_number,
            )

        if hasattr(instance, "_notification_restitution_required"):
            delattr(instance, "_notification_restitution_required")
