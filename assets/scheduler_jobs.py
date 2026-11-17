"""
Notification scheduling jobs for APScheduler
Handles automated reminders and monitoring for material loans
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from assets.models import Attribution, NotificationLog, NotificationPreferences
from assets.email_service import NotificationEmailService

logger = logging.getLogger(__name__)


def check_court_terme_reminders():
    """
    Check and send reminders for short-term loans (< 4 hours)
    Sends notification at 2 hours before return time
    Called every 30 minutes
    """
    try:
        now = timezone.now()
        
        # Find attributions with court terme loans that need reminders
        # Not yet returned and within 2.5 hours of return time
        attributions = Attribution.objects.filter(
            type_attribution=Attribution.TYPE_TEMPORAIRE,
            duree_emprunt=Attribution.DUREE_COURT_TERME,
            date_retour_effective__isnull=True,  # Not returned yet
        ).select_related('client', 'materiel')
        
        reminder_sent_count = 0
        
        for attribution in attributions:
            if attribution.retour_echeance() is None:
                continue
            
            # Calculate time until return
            return_datetime = attribution.retour_echeance()
            
            time_until_return = return_datetime - now
            
            # Send reminder if within 2.5 hour window and not yet sent
            if timedelta(minutes=0) <= time_until_return <= timedelta(hours=2, minutes=30):
                _send_reminder_notification(
                    attribution,
                    NotificationLog.TYPE_RAPPEL_2H,
                    reason="Court terme 2h before return"
                )
                reminder_sent_count += 1
        
        logger.info(f"Court terme reminders: {reminder_sent_count} sent")
        
    except Exception as e:
        logger.error(f"Error in check_court_terme_reminders: {e}", exc_info=True)


def check_moyen_terme_reminders():
    """
    Check and send reminders for medium-term loans (4-24 hours)
    Sends notification at 2 hours before return time
    Called every 12 hours
    """
    try:
        now = timezone.now()
        
        attributions = Attribution.objects.filter(
            type_attribution=Attribution.TYPE_TEMPORAIRE,
            duree_emprunt=Attribution.DUREE_MOYEN_TERME,
            date_retour_effective__isnull=True,
        ).select_related('client', 'materiel')
        
        reminder_sent_count = 0
        
        for attribution in attributions:
            if attribution.retour_echeance() is None:
                continue
            
            return_datetime = attribution.retour_echeance()
            
            time_until_return = return_datetime - now
            
            # Send reminder if within 2.5 hour window
            if timedelta(minutes=0) <= time_until_return <= timedelta(hours=2, minutes=30):
                _send_reminder_notification(
                    attribution,
                    NotificationLog.TYPE_RAPPEL_2H,
                    reason="Moyen terme 2h before return"
                )
                reminder_sent_count += 1
        
        logger.info(f"Moyen terme reminders: {reminder_sent_count} sent")
        
    except Exception as e:
        logger.error(f"Error in check_moyen_terme_reminders: {e}", exc_info=True)


def check_long_terme_reminders():
    """
    Check and send reminders for long-term loans (> 24 hours)
    Sends notifications at J-2 (2 days before), J-1 (day before), and morning-of
    Called daily at 8:00 AM
    """
    try:
        now = timezone.now()
        today = timezone.localdate(now)
        
        attributions = Attribution.objects.filter(
            type_attribution=Attribution.TYPE_TEMPORAIRE,
            duree_emprunt=Attribution.DUREE_LONG_TERME,
            date_retour_effective__isnull=True,
        ).select_related('client', 'materiel')
        
        reminder_counts = {
            'j_moins_2': 0,
            'j_moins_1': 0,
            'final': 0,
        }
        
        for attribution in attributions:
            if attribution.date_retour_prevue is None:
                continue
            
            days_until_return = (attribution.date_retour_prevue - today).days
            
            # J-2 reminder (2 days before)
            if days_until_return == 2:
                _send_reminder_notification(
                    attribution,
                    NotificationLog.TYPE_RAPPEL_J_MOINS_2,
                    reason="Long terme J-2"
                )
                reminder_counts['j_moins_2'] += 1
            
            # J-1 reminder (1 day before)
            elif days_until_return == 1:
                _send_reminder_notification(
                    attribution,
                    NotificationLog.TYPE_RAPPEL_J_MOINS_1,
                    reason="Long terme J-1"
                )
                reminder_counts['j_moins_1'] += 1
            
            # Final reminder (morning of return day)
            elif days_until_return == 0:
                _send_reminder_notification(
                    attribution,
                    NotificationLog.TYPE_RAPPEL_FINAL,
                    reason="Long terme final"
                )
                reminder_counts['final'] += 1
        
        logger.info(f"Long terme reminders - J-2: {reminder_counts['j_moins_2']}, "
                   f"J-1: {reminder_counts['j_moins_1']}, "
                   f"Final: {reminder_counts['final']}")
        
    except Exception as e:
        logger.error(f"Error in check_long_terme_reminders: {e}", exc_info=True)


def check_overdue_materials():
    """
    Check for overdue materials and send alert notifications
    For materials not returned by expected return time
    Called every 15 minutes
    """
    try:
        now = timezone.now()
        
        # Find attributions that are overdue
        attributions = Attribution.objects.filter(
            type_attribution=Attribution.TYPE_TEMPORAIRE,
            date_retour_effective__isnull=True,  # Not returned yet
            date_retour_prevue__lt=timezone.localdate(now),  # Return date has passed
        ).select_related('client', 'materiel')
        
        # Also check current day but past return time
        attributions_today = Attribution.objects.filter(
            type_attribution=Attribution.TYPE_TEMPORAIRE,
            date_retour_effective__isnull=True,
            date_retour_prevue=timezone.localdate(now),
        ).select_related('client', 'materiel')
        
        for attribution in list(attributions) + list(attributions_today):
            if attribution.is_overdue():
                _send_overdue_notification(attribution, (timezone.localdate(now) - attribution.date_retour_prevue).days)

        logger.info("Overdue materials check completed")
        
    except Exception as e:
        logger.error(f"Error in check_overdue_materials: {e}", exc_info=True)


def cleanup_old_notifications(days=90):
    """
    Clean up old notification logs older than specified days
    Removes completed/failed notifications older than 90 days
    Called daily at 2:00 AM
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        deleted_count, _ = NotificationLog.objects.filter(
            date_envoi__lt=cutoff_date,
            statut__in=[
                NotificationLog.STATUT_ENVOYEE,
                NotificationLog.STATUT_ECHEC_PERMANENT,
            ]
        ).delete()
        
        logger.info(f"Cleanup: Deleted {deleted_count} old notification logs")
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_notifications: {e}", exc_info=True)


def _send_reminder_notification(attribution, reminder_type, reason=""):
    """Deliver independently to the borrower and the responsible employee."""
    from django.db import transaction
    with transaction.atomic():
        loan = Attribution.objects.select_for_update().get(pk=attribution.pk)
        if loan.date_retour_effective is not None:
            return
        recipients = {}
        client = loan.client
        if client and client.email:
            prefs = NotificationPreferences.objects.filter(client=client).first()
            if not prefs or prefs.notifications_email:
                recipients[client.email.strip().lower()] = NotificationEmailService.ROLE_RECEVEUR
        lender = loan.employe_responsable
        if lender and lender.is_active and lender.email:
            recipients[lender.email.strip().lower()] = NotificationEmailService.ROLE_PRETEUR
        now = timezone.now()
        for email, role in recipients.items():
            if not email:
                continue
            logs = NotificationLog.objects.filter(
                attribution=loan, type_notification=reminder_type,
                canal=NotificationLog.CANAL_EMAIL, destinataire__iexact=email,
            ).order_by('-date_envoi')
            if reminder_type == NotificationLog.TYPE_RETARD:
                logs = logs.filter(date_envoi__gte=now - timedelta(days=1))
            if logs.filter(statut=NotificationLog.STATUT_ENVOYEE).exists():
                continue
            if logs.count() >= 3:
                continue
            latest = logs.first()
            if latest and now - latest.date_envoi < timedelta(minutes=15):
                continue
            notification = NotificationLog.objects.create(
                attribution=loan, type_notification=reminder_type,
                canal=NotificationLog.CANAL_EMAIL, duree_emprunt=loan.duree_emprunt,
                destinataire=email, statut=NotificationLog.STATUT_EN_ATTENTE,
            )
            NotificationEmailService.send_notification(notification, recipient_role=role)


def _send_overdue_notification(attribution, days_late):
    _send_reminder_notification(attribution, NotificationLog.TYPE_RETARD)
