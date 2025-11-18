# assets/signals.py
"""
Signaux Django pour les alertes
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Alerte
from .email_service import EmailAlerteService


@receiver(post_save, sender=Alerte)
def envoyer_email_alerte_critique(sender, instance, created, **kwargs):
    """Envoie un email automatiquement lorsqu'une alerte critique est créée"""
    if created and instance.severite == Alerte.SEVERITE_CRITICAL:
        # Envoyer l'email de manière asynchrone (ou synchrone en développement)
        try:
            EmailAlerteService.envoyer_alerte_critique(instance)
        except Exception as e:
            # Logger l'erreur mais ne pas bloquer la création de l'alerte
            print(f"Erreur lors de l'envoi de l'email d'alerte: {e}")

