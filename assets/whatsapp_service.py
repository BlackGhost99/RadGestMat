"""
WhatsApp notification service for RadGestMat
Integrates with Twilio for sending WhatsApp messages
"""
import logging
from django.conf import settings
from assets.models import NotificationLog
from assets.whatsapp_templates import WhatsAppTemplates

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

logger = logging.getLogger(__name__)


class WhatsAppNotificationService:
    """
    Service for sending WhatsApp notifications via Twilio
    """
    
    _twilio_client = None
    
    @classmethod
    def _get_twilio_client(cls):
        """Get or initialize Twilio client"""
        if cls._twilio_client is None:
            if not TWILIO_AVAILABLE:
                logger.error("Twilio SDK not installed. Install with: pip install twilio")
                return None
            
            try:
                account_sid = settings.TWILIO_ACCOUNT_SID
                auth_token = settings.TWILIO_AUTH_TOKEN
                
                if not account_sid or not auth_token:
                    logger.error("Twilio credentials not configured in settings")
                    return None
                
                cls._twilio_client = Client(account_sid, auth_token)
            except AttributeError:
                logger.error("TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not configured")
                return None
        
        return cls._twilio_client
    
    @staticmethod
    def send_notification(notification_log):
        """
        Send WhatsApp notification
        
        Args:
            notification_log: NotificationLog instance
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            client = WhatsAppNotificationService._get_twilio_client()
            if client is None:
                logger.warning(f"Twilio client unavailable for notification {notification_log.id}")
                return False
            
            # Get message content
            subject = WhatsAppNotificationService._get_subject(notification_log)
            message_body = WhatsAppNotificationService._get_message_body(notification_log)
            
            # Format message with subject and body
            full_message = f"*{subject}*\n\n{message_body}"
            
            # Get recipient phone number
            recipient_phone = notification_log.destinataire
            if not recipient_phone or '@' in recipient_phone:
                # If no valid phone or email address, skip
                logger.warning(f"Invalid phone number for WhatsApp: {recipient_phone}")
                notification_log.statut = NotificationLog.STATUT_ECHEC_PERMANENT
                notification_log.erreur_message = "Invalid recipient phone number"
                notification_log.save(update_fields=['statut', 'erreur_message'])
                return False
            
            # Ensure phone number starts with +
            if not recipient_phone.startswith('+'):
                recipient_phone = '+' + recipient_phone
            
            # Get Twilio WhatsApp number
            twilio_phone = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)
            if not twilio_phone:
                logger.error("TWILIO_WHATSAPP_FROM not configured in settings")
                notification_log.statut = NotificationLog.STATUT_ECHEC_PERMANENT
                notification_log.erreur_message = "Twilio WhatsApp sender not configured"
                notification_log.save(update_fields=['statut', 'erreur_message'])
                return False
            
            # Send message
            message = client.messages.create(
                from_=f"whatsapp:{twilio_phone}",
                body=full_message,
                to=f"whatsapp:{recipient_phone}"
            )
            
            # Update notification log
            notification_log.statut = NotificationLog.STATUT_ENVOYEE
            notification_log.date_envoi = __import__('django.utils.timezone', fromlist=['now']).now()
            notification_log.save(update_fields=['statut', 'date_envoi'])
            
            logger.info(f"WhatsApp message {message.sid} sent to {recipient_phone} "
                       f"for notification {notification_log.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp notification {notification_log.id}: {e}", 
                        exc_info=True)
            
            # Update notification log with error
            notification_log.statut = NotificationLog.STATUT_ECHEC
            notification_log.erreur_message = str(e)
            notification_log.nb_tentatives = (notification_log.nb_tentatives or 0) + 1
            
            # Mark as permanent failure after 3 attempts
            if notification_log.nb_tentatives >= 3:
                notification_log.statut = NotificationLog.STATUT_ECHEC_PERMANENT
            
            notification_log.save(update_fields=['statut', 'erreur_message', 'nb_tentatives'])
            return False
    
    @staticmethod
    def _get_subject(notification_log):
        """Get message subject based on notification type"""
        subjects = {
            NotificationLog.TYPE_CREATION: "✅ Emprunt Confirmé",
            NotificationLog.TYPE_RAPPEL_2H: "⏰ Rappel: 2 heures avant la restitution",
            NotificationLog.TYPE_RAPPEL_J_MOINS_2: "📋 Rappel: Restitution dans 2 jours",
            NotificationLog.TYPE_RAPPEL_J_MOINS_1: "🚨 Rappel Urgent: Restitution demain",
            NotificationLog.TYPE_RAPPEL_FINAL: "🔴 CRITIQUE: Restitution AUJOURD'HUI",
            NotificationLog.TYPE_RETARD: "⚠️ ALERTE: Matériel en RETARD",
            NotificationLog.TYPE_RESTITUTION: "✨ Matériel Restitué",
        }
        return subjects.get(notification_log.type_notification, "Notification RadGestMat")
    
    @staticmethod
    def _get_message_body(notification_log):
        """Get message body based on notification type"""
        templates = WhatsAppTemplates()
        attribution = notification_log.attribution
        
        context = {
            'attribution': attribution,
            'materiel': attribution.materiel,
            'client': attribution.client,
            'duree_emprunt': attribution.duree_emprunt,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        template_map = {
            NotificationLog.TYPE_CREATION: 'creation',
            NotificationLog.TYPE_RAPPEL_2H: 'rappel_2h',
            NotificationLog.TYPE_RAPPEL_J_MOINS_2: 'rappel_j2',
            NotificationLog.TYPE_RAPPEL_J_MOINS_1: 'rappel_j1',
            NotificationLog.TYPE_RAPPEL_FINAL: 'rappel_final',
            NotificationLog.TYPE_RETARD: 'retard',
            NotificationLog.TYPE_RESTITUTION: 'restitution',
        }
        
        template_name = template_map.get(notification_log.type_notification, 'creation')
        return getattr(templates, template_name)(**context)
    
    @staticmethod
    def send_creation_notification(attribution, phone_number, client_type='client'):
        """Send creation confirmation via WhatsApp"""
        try:
            notification = NotificationLog.objects.create(
                attribution=attribution,
                type_notification=NotificationLog.TYPE_CREATION,
                canal=NotificationLog.CANAL_WHATSAPP,
                duree_emprunt=attribution.duree_emprunt,
                destinataire=phone_number,
                statut=NotificationLog.STATUT_EN_ATTENTE,
            )
            return WhatsAppNotificationService.send_notification(notification)
        except Exception as e:
            logger.error(f"Error in send_creation_notification: {e}")
            return False
    
    @staticmethod
    def send_reminder_notification(attribution, reminder_type, phone_number):
        """Send reminder via WhatsApp"""
        try:
            notification = NotificationLog.objects.create(
                attribution=attribution,
                type_notification=reminder_type,
                canal=NotificationLog.CANAL_WHATSAPP,
                duree_emprunt=attribution.duree_emprunt,
                destinataire=phone_number,
                statut=NotificationLog.STATUT_EN_ATTENTE,
            )
            return WhatsAppNotificationService.send_notification(notification)
        except Exception as e:
            logger.error(f"Error in send_reminder_notification: {e}")
            return False
    
    @staticmethod
    def send_overdue_alert(attribution, phone_number, days_late=0):
        """Send overdue alert via WhatsApp"""
        try:
            notification = NotificationLog.objects.create(
                attribution=attribution,
                type_notification=NotificationLog.TYPE_RETARD,
                canal=NotificationLog.CANAL_WHATSAPP,
                duree_emprunt=attribution.duree_emprunt,
                destinataire=phone_number,
                statut=NotificationLog.STATUT_EN_ATTENTE,
            )
            return WhatsAppNotificationService.send_notification(notification)
        except Exception as e:
            logger.error(f"Error in send_overdue_alert: {e}")
            return False
    
    @staticmethod
    def send_restitution_notification(attribution, phone_number):
        """Send restitution confirmation via WhatsApp"""
        try:
            notification = NotificationLog.objects.create(
                attribution=attribution,
                type_notification=NotificationLog.TYPE_RESTITUTION,
                canal=NotificationLog.CANAL_WHATSAPP,
                duree_emprunt=attribution.duree_emprunt,
                destinataire=phone_number,
                statut=NotificationLog.STATUT_EN_ATTENTE,
            )
            return WhatsAppNotificationService.send_notification(notification)
        except Exception as e:
            logger.error(f"Error in send_restitution_notification: {e}")
            return False
