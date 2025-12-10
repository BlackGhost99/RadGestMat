#!/usr/bin/env python
"""
Test WhatsApp Direct - Send messages without creating attribution
Just test the WhatsApp service directly
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


def test_direct_whatsapp():
    """Send WhatsApp messages directly"""
    
    phone_number = '+24165339274'
    
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " TEST WHATSAPP DIRECT - RADGESTMAT ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    print("\n🔍 VÉRIFICATION CONFIGURATION TWILIO")
    print("=" * 80)
    
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    whatsapp_from = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)
    
    if not account_sid or not auth_token:
        print("❌ Configuration Twilio manquante!")
        return False
    
    print(f"✓ Account SID: {account_sid[:10]}...{account_sid[-10:]}")
    print(f"✓ Auth Token: {'*' * 20}")
    print(f"✓ WhatsApp From: {whatsapp_from}")
    
    try:
        client = Client(account_sid, auth_token)
        
        # Message 1: Attribution Creation
        print(f"\n📧 Envoi message 1: CRÉATION D'ATTRIBUTION")
        print("=" * 80)
        
        message1_body = """✅ Confirmation d'Emprunt

📦 Matériel: Ordinateur Portable Test
🏷️ Référence: TEST-LAPTOP-001
📅 Date retour: 2025-12-10
🕐 Heure retour: 17:00 

✅ Vous pouvez retirer le matériel.

RadGestMat - Système de gestion"""
        
        msg1 = client.messages.create(
            from_=whatsapp_from,
            body=message1_body,
            to=f'whatsapp:{phone_number}'
        )
        
        print(f"✅ Message 1 envoyé!")
        print(f"   SID: {msg1.sid}")
        print(f"   Status: {msg1.status}")
        
        # Message 2: Reminder 2h before
        print(f"\n📧 Envoi message 2: RAPPEL (2h avant)")
        print("=" * 80)
        
        message2_body = """⏰ Rappel: Retour du matériel dans 2h!

📦 Matériel: Ordinateur Portable Test
⏱️ Retour prévu: Aujourd'hui 17:00

Merci de retourner le matériel à temps.

RadGestMat"""
        
        msg2 = client.messages.create(
            from_=whatsapp_from,
            body=message2_body,
            to=f'whatsapp:{phone_number}'
        )
        
        print(f"✅ Message 2 envoyé!")
        print(f"   SID: {msg2.sid}")
        print(f"   Status: {msg2.status}")
        
        # Results
        print(f"\n" + "=" * 80)
        print("✅ TEST TERMINÉ!")
        print("=" * 80)
        print(f"\n📱 Vous devriez recevoir 2 messages sur: {phone_number}")
        print(f"1️⃣  Message de CRÉATION")
        print(f"2️⃣  Message de RAPPEL (2h avant)")
        print(f"\n🔔 Vérifiez votre WhatsApp dans 10 secondes...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_direct_whatsapp()
