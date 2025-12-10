"""
WhatsApp message templates for RadGestMat
Text-based templates for all notification types
"""


class WhatsAppTemplates:
    """
    WhatsApp message templates
    Each method returns a formatted message string
    """
    
    @staticmethod
    def creation(attribution, materiel, client, duree_emprunt, **kwargs):
        """
        Message sent when material is borrowed
        """
        return f"""Bonjour {client.first_name or client.name}! 👋

Votre demande d'emprunt a été confirmée:

📦 *Matériel:* {materiel.nom}
🏷️ *Référence:* {materiel.code}
📅 *Date retour:* {attribution.date_retour_prevue}
🕐 *Heure retour:* {attribution.heure_retour_prevue or 'À convenir'}

✅ Vous pouvez retirer le matériel au point de distribution.

Pour toute question, contactez-nous!"""
    
    @staticmethod
    def rappel_2h(attribution, materiel, client, duree_emprunt, **kwargs):
        """
        Reminder sent 2 hours before return time
        For short and medium term loans
        """
        return f"""⏰ *RAPPEL - 2 heures avant la restitution!*

Bonjour {client.first_name or client.name},

Vous devez restituer le matériel suivant dans 2 heures:

📦 *Matériel:* {materiel.nom}
🏷️ *Référence:* {materiel.code}
🕐 *Heure limite:* {attribution.heure_retour_prevue}

⚠️ Vérifiez que le matériel est en bon état avant la restitution.

📍 Apportez le matériel au point de retour."""
    
    @staticmethod
    def rappel_j2(attribution, materiel, client, duree_emprunt, **kwargs):
        """
        Reminder sent 2 days before return
        For long term loans
        """
        return f"""📋 *RAPPEL - Restitution dans 2 jours*

Bonjour {client.first_name or client.name},

Vous avez emprunté un matériel qui doit être restitué dans 2 jours:

📦 *Matériel:* {materiel.nom}
🏷️ *Référence:* {materiel.code}
📅 *Date retour:* {attribution.date_retour_prevue}
🕐 *Heure retour:* {attribution.heure_retour_prevue or 'Avant 18h'}

Préparez le matériel et vérifiez son état.

✅ Tous les accessoires doivent être inclus."""
    
    @staticmethod
    def rappel_j1(attribution, materiel, client, duree_emprunt, **kwargs):
        """
        Reminder sent 1 day before return
        For long term loans - URGENT
        """
        return f"""🚨 *RAPPEL URGENT - Restitution DEMAIN!*

Bonjour {client.first_name or client.name},

Votre emprunt expire DEMAIN:

📦 *Matériel:* {materiel.nom}
🏷️ *Référence:* {materiel.code}
📅 *Date retour:* {attribution.date_retour_prevue}
🕐 *Heure limite:* {attribution.heure_retour_prevue or 'Avant 18h'}

⚠️ *Actions requises:*
• Arrêtez l'utilisation du matériel
• Nettoyez le matériel
• Vérifiez tous les accessoires

❌ Le dépassement peut entraîner des frais de retard."""
    
    @staticmethod
    def rappel_final(attribution, materiel, client, duree_emprunt, **kwargs):
        """
        Final reminder sent on day of return
        For long term loans - CRITICAL
        """
        return f"""🔴 *CRITIQUE - RESTITUTION AUJOURD'HUI!*

URGENT {client.first_name or client.name}!

Le matériel DOIT être restitué AUJOURD'HUI:

📦 *Matériel:* {materiel.nom}
🏷️ *Référence:* {materiel.code}
⏰ *Heure limite:* {attribution.heure_retour_prevue or 'Avant 18h'}

🚨 *CONSÉQUENCES du dépassement:*
• Frais de retard applicables
• Pénalités de non-restitution
• Restriction d'emprunt futur

✅ Apportez le matériel AU PLUS TÔT au point de retour."""
    
    @staticmethod
    def retard(attribution, materiel, client, duree_emprunt, **kwargs):
        """
        Alert for overdue material
        Sent when material is not returned by deadline
        """
        return f"""⚠️ *ALERTE - MATÉRIEL EN RETARD*

{client.first_name or client.name},

Le matériel suivant est EN RETARD:

📦 *Matériel:* {materiel.nom}
🏷️ *Référence:* {materiel.code}
📅 *Date retour prévue:* {attribution.date_retour_prevue}

🚨 *Situation actuelle:*
• Matériel non restitué
• Retard en cours
• Frais appliqués

✅ *Action immédiate requise:*
Restituez le matériel dès que possible!

Pour tout problème, contactez-nous immédiatement."""
    
    @staticmethod
    def restitution(attribution, materiel, client, duree_emprunt, **kwargs):
        """
        Confirmation when material is returned
        Sent after successful return
        """
        return f"""✨ *MATÉRIEL RESTITUÉ - MERCI!*

Bonjour {client.first_name or client.name},

Votre emprunt a été officiellement clôturé:

📦 *Matériel:* {materiel.nom}
🏷️ *Référence:* {materiel.code}
✅ *Statut:* Restitué avec succès

📊 *Détails de l'emprunt:*
• Durée: {duree_emprunt}
• Restitué le: {attribution.heure_retour_effective or 'À confirmer'}

Merci d'avoir utilisé notre service de gestion des matériels!

📈 Vous pouvez à nouveau faire une demande d'emprunt.
👍 Bon travail!"""
