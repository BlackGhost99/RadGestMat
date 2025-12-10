#!/usr/bin/env python
"""
Quick Twilio WhatsApp Test Script
Test direct WhatsApp message to +241 62308363
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


def test_twilio_config():
    """Test if Twilio is configured"""
    print("=" * 80)
    print("🔍 VÉRIFICATION CONFIGURATION TWILIO")
    print("=" * 80)
    
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    whatsapp_from = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)
    
    print(f"\n✓ Account SID: {account_sid[:10]}...{account_sid[-10:] if account_sid else 'MANQUANT'}")
    print(f"✓ Auth Token: {'*' * 20 if auth_token and auth_token != '[AuthToken]' else '❌ MANQUANT ou PLACEHOLDER'}")
    print(f"✓ WhatsApp From: {whatsapp_from}")
    
    if not account_sid or not auth_token or auth_token == '[AuthToken]':
        print("\n❌ Configuration incomplète!")
        print("\n📝 ÉTAPES:")
        print("1. Allez sur: https://www.twilio.com/console")
        print("2. Cliquez sur le cadenas à côté de votre Account SID")
        print("3. Cliquez sur 'Show' pour afficher votre Auth Token")
        print("4. Copiez le token et remplacez [AuthToken] dans:")
        print("   radgestmat/settings/development.py")
        return False
    
    return True


def send_test_message():
    """Send a test WhatsApp message"""
    print("\n" + "=" * 80)
    print("📤 ENVOI MESSAGE TEST")
    print("=" * 80)
    
    try:
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        
        # Create Twilio client
        client = Client(account_sid, auth_token)
        
        print(f"\n🔌 Connexion à Twilio...")
        
        # Send message
        message = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            body='✅ Test RadGestMat - Système de notifications WhatsApp fonctionnel! 🎉',
            to='whatsapp:+24162308363'
        )
        
        print(f"✅ Message envoyé avec succès!")
        print(f"   Message SID: {message.sid}")
        print(f"   Status: {message.status}")
        print(f"   To: +24162308363")
        
        print(f"\n🔔 Vérifiez votre WhatsApp (+241 62308363)")
        print(f"   Vous devriez recevoir un message dans les 5-10 secondes...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'envoi: {str(e)}")
        print(f"\n💡 Vérifiez:")
        print(f"   1. Votre Auth Token est correct")
        print(f"   2. Vous avez rejoint le sandbox WhatsApp")
        print(f"      (Envoyez 'join <code>' au numéro +1 415 523 8886)")
        return False


def main():
    """Main test function"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " TEST TWILIO WHATSAPP POUR RADGESTMAT ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Step 1: Check configuration
    if not test_twilio_config():
        print("\n❌ Configuration incomplète. Arrêt.")
        return False
    
    # Step 2: Send test message
    input("\n⏳ Appuyez sur ENTRÉE pour envoyer un message test...")
    
    if not send_test_message():
        print("\n❌ Impossible d'envoyer le message.")
        return False
    
    print("\n" + "=" * 80)
    print("✅ TEST TERMINÉ!")
    print("=" * 80)
    print("\n📊 Prochaines étapes:")
    print("   1. Vérifiez votre WhatsApp")
    print("   2. Si vous recevez le message: Le système fonctionne! ✅")
    print("   3. Sinon: Vérifiez que vous avez rejoint le Sandbox WhatsApp")
    print("      Commande: Envoyez 'join <code>' à +1 415 523 8886")
    
    return True


if __name__ == '__main__':
    main()
