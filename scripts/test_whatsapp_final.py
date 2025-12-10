#!/usr/bin/env python
"""
Test WhatsApp Final - With correct phone number
Send to +24105339274 (the number that received the sandbox message)
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'radgestmat.settings.development')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.conf import settings
from twilio.rest import Client


def test_correct_number():
    """Send WhatsApp to the CORRECT number (+24105339274)"""
    
    # LE BON NUMÉRO - celui qui a reçu le message sandbox
    phone_number = '+24105339274'
    
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " TEST WHATSAPP - BON NUMÉRO ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    print(f"\n📱 Numéro cible: {phone_number}")
    print("   (C'est le numéro qui a reçu le message du sandbox)")
    
    try:
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        whatsapp_from = settings.TWILIO_WHATSAPP_FROM
        
        client = Client(account_sid, auth_token)
        
        # Message simple et direct
        print(f"\n📧 Envoi du message test...")
        print("=" * 80)
        
        message_body = """🎉 TEST RADGESTMAT - WhatsApp fonctionne!

✅ Si vous recevez ce message, le système de notification WhatsApp est OPÉRATIONNEL!

📦 Exemple: Attribution matériel
🔔 Rappel automatique
⏰ Notification de retard

RadGestMat - Système de gestion"""
        
        msg = client.messages.create(
            from_=whatsapp_from,
            body=message_body,
            to=f'whatsapp:{phone_number}'
        )
        
        print(f"✅ Message envoyé avec succès!")
        print(f"   Message SID: {msg.sid}")
        print(f"   Status: {msg.status}")
        print(f"   To: {phone_number}")
        
        print(f"\n" + "=" * 80)
        print("✅ TEST TERMINÉ!")
        print("=" * 80)
        print(f"\n🔔 Vérifiez WhatsApp sur: {phone_number}")
        print(f"   Vous devriez recevoir le message dans 5-10 secondes!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_correct_number()
