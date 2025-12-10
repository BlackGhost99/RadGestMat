# assets/signals.py
"""
Signaux Django pour les alertes et notifications d'attribution

Ce module gère l'envoi automatique de notifications lors de:
- Création d'une attribution → Notification de création
- Retour de matériel → Confirmation de restitution
- Alertes critiques → Email d'alerte
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Alerte, Attribution, NotificationPreferences
from .email_service import EmailAlerteService, NotificationEmailService
from .whatsapp_service import WhatsAppNotificationService

logger = logging.getLogger(__name__)


# ============================================================================
# SIGNAUX POUR LES ALERTES CRITIQUES
# ============================================================================

@receiver(post_save, sender=Alerte)
def envoyer_email_alerte_critique(sender, instance, created, **kwargs):
    """Envoie un email automatiquement lorsqu'une alerte critique est créée"""
    if created and instance.severite == Alerte.SEVERITE_CRITICAL:
        # Envoyer l'email de manière asynchrone (ou synchrone en développement)
        try:
            EmailAlerteService.envoyer_alerte_critique(instance)
        except Exception as e:
            # Logger l'erreur mais ne pas bloquer la création de l'alerte
            logger.error(f"Erreur lors de l'envoi de l'email d'alerte: {e}", exc_info=True)


# ============================================================================
# SIGNAUX POUR LES NOTIFICATIONS D'ATTRIBUTION
# ============================================================================

@receiver(pre_save, sender=Attribution)
def detecter_retour_materiel(sender, instance, **kwargs):
    """
    Détecte si le matériel vient d'être retourné (date_retour_effective définie)
    et marque l'instance pour envoi de notification dans post_save
    """
    if instance.pk:  # L'attribution existe déjà
        try:
            old_instance = Attribution.objects.get(pk=instance.pk)
            # Si date_retour_effective vient d'être définie
            if not old_instance.date_retour_effective and instance.date_retour_effective:
                instance._notification_restitution_required = True
            else:
                instance._notification_restitution_required = False
        except Attribution.DoesNotExist:
            instance._notification_restitution_required = False
    else:
        instance._notification_restitution_required = False


@receiver(post_save, sender=Attribution)
def envoyer_notifications_attribution(sender, instance, created, **kwargs):
    """
    Envoie automatiquement les notifications lors de:
    1. Création d'une attribution → Notification de création
    2. Retour de matériel → Confirmation de restitution
    
    Les notifications sont envoyées selon les préférences de l'utilisateur:
    - Email (par défaut activé)
    - WhatsApp (si activé et numéro configuré)
    """
    # Récupérer les préférences du client
    try:
        preferences, _ = NotificationPreferences.objects.get_or_create(
            client=instance.client
        )
    except Exception as e:
        logger.error(f"Impossible de récupérer les préférences pour {instance.client}: {e}")
        # Créer des préférences par défaut (email activé)
        preferences = type('obj', (object,), {
            'notifications_email': True,
            'notifications_whatsapp': False,
            'phone_number': None
        })()

    # ========================================
    # 1. NOTIFICATION DE CRÉATION
    # ========================================
    if created:
        logger.info(f"📧 Nouvelle attribution créée: {instance.id} - Envoi des notifications...")
        
        # Email de création (si activé)
        if preferences.notifications_email and instance.client.email:
            try:
                # Créer le log de notification
                from .models import NotificationLog
                log = NotificationLog.objects.create(
                    attribution=instance,
                    type_notification=NotificationLog.TYPE_CREATION,
                    canal='EMAIL',
                    duree_emprunt=instance.duree_emprunt,
                    destinataire=instance.client.email,
                    statut='EN_ATTENTE'
                )
                # Envoyer via le service
                NotificationEmailService.send_notification(log)
                logger.info(f"✅ Email de création envoyé à {instance.client.email}")
            except Exception as e:
                logger.error(f"❌ Erreur email création: {e}", exc_info=True)
        
        # WhatsApp de création (si activé)
        if preferences.notifications_whatsapp and preferences.phone_number:
            try:
                # Créer le log de notification
                from .models import NotificationLog
                log = NotificationLog.objects.create(
                    attribution=instance,
                    type_notification=NotificationLog.TYPE_CREATION,
                    canal='WHATSAPP',
                    duree_emprunt=instance.duree_emprunt,
                    destinataire=preferences.phone_number,
                    statut='EN_ATTENTE'
                )
                # Envoyer via le service
                WhatsAppNotificationService.send_notification(log)
                logger.info(f"✅ WhatsApp de création envoyé à {preferences.phone_number}")
            except Exception as e:
                logger.error(f"❌ Erreur WhatsApp création: {e}", exc_info=True)

    # ========================================
    # 2. CONFIRMATION DE RESTITUTION
    # ========================================
    elif hasattr(instance, '_notification_restitution_required') and instance._notification_restitution_required:
        logger.info(f"📦 Matériel retourné pour attribution {instance.id} - Envoi des confirmations...")
        
        # Email de restitution (si activé)
        if preferences.notifications_email and instance.client.email:
            try:
                # Créer le log de notification
                from .models import NotificationLog
                log = NotificationLog.objects.create(
                    attribution=instance,
                    type_notification=NotificationLog.TYPE_RESTITUTION,
                    canal='EMAIL',
                    duree_emprunt=instance.duree_emprunt,
                    destinataire=instance.client.email,
                    statut='EN_ATTENTE'
                )
                # Envoyer via le service
                NotificationEmailService.send_notification(log)
                logger.info(f"✅ Email de restitution envoyé à {instance.client.email}")
            except Exception as e:
                logger.error(f"❌ Erreur email restitution: {e}", exc_info=True)
        
        # WhatsApp de restitution (si activé)
        if preferences.notifications_whatsapp and preferences.phone_number:
            try:
                # Créer le log de notification
                from .models import NotificationLog
                log = NotificationLog.objects.create(
                    attribution=instance,
                    type_notification=NotificationLog.TYPE_RESTITUTION,
                    canal='WHATSAPP',
                    duree_emprunt=instance.duree_emprunt,
                    destinataire=preferences.phone_number,
                    statut='EN_ATTENTE'
                )
                # Envoyer via le service
                WhatsAppNotificationService.send_notification(log)
                logger.info(f"✅ WhatsApp de restitution envoyé à {preferences.phone_number}")
            except Exception as e:
                logger.error(f"❌ Erreur WhatsApp restitution: {e}", exc_info=True)
        
        # Nettoyer le flag
        delattr(instance, '_notification_restitution_required')

