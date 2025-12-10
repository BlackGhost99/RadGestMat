#!/usr/bin/env python
"""
Test WhatsApp Real - Attribution Notifications
Test both scenarios: User (agent) and Client (recipient)
Target: +241 65339274
"""

import os
import sys
import django
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'radgestmat.settings.development')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from assets.models import (
    Materiel, 
    Client, 
    Attribution, 
    NotificationLog,
    Categorie,
    Departement
)
from assets.whatsapp_service import WhatsAppNotificationService

User = get_user_model()


def cleanup_test_data():
    """Clean up test data from previous runs"""
    print("\n🧹 Nettoyage des données de test précédentes...")
    
    # Delete test attributions
    Attribution.objects.filter(
        raison__startswith='TEST WHATSAPP'
    ).delete()
    
    # Delete test materials
    Materiel.objects.filter(
        code__startswith='TEST-WHATSAPP'
    ).delete()
    
    # Delete test clients
    Client.objects.filter(
        phone='+24165339274'
    ).delete()
    
    print("✅ Nettoyage terminé")


def setup_test_data():
    """Setup test data for attribution"""
    print("\n📊 ÉTAPE 1: Préparation des données de test")
    print("=" * 80)
    
    # Get or create department
    dept, _ = Departement.objects.get_or_create(
        code='TEST',
        defaults={'nom': 'Département Test', 'description': 'Test Department'}
    )
    print(f"✓ Département: {dept.nom}")
    
    # Get or create category
    category, _ = Categorie.objects.get_or_create(
        nom='Catégorie Test',
        departement=dept,
        defaults={'description': 'Test Category'}
    )
    print(f"✓ Catégorie: {category.nom}")
    
    # Get or create material
    materiel, _ = Materiel.objects.get_or_create(
        numero_inventaire='TEST-WHATSAPP-LAPTOP-001',
        defaults={
            'asset_id': 'TEST-WHATSAPP-LAPTOP',
            'nom': 'Ordinateur Portable Test WhatsApp',
            'categorie': category,
            'departement': dept,
            'marque': 'Test Brand',
            'modele': 'Test Model',
            'numero_serie': 'TEST-001-WHATSAPP',
            'etat_technique': Materiel.ETAT_FONCTIONNEL,
            'statut_disponibilite': Materiel.STATUT_DISPONIBLE,
            'description': 'Matériel de test pour notifications WhatsApp'
        }
    )
    print(f"✓ Matériel: {materiel.nom}")
    
    # Get or create client
    client, _ = Client.objects.get_or_create(
        telephone='+24165339274',
        defaults={
            'nom': 'Client Test WhatsApp',
            'email': 'test.whatsapp@example.com'
        }
    )
    print(f"✓ Client: {client.nom}")
    
    # Get or create user
    user, _ = User.objects.get_or_create(
        username='test_whatsapp_user',
        defaults={
            'first_name': 'Test',
            'last_name': 'WhatsApp',
            'email': 'test.user@example.com'
        }
    )
    print(f"✓ Utilisateur: {user.get_full_name()}")
    
    return {
        'materiel': materiel,
        'client': client,
        'user': user,
        'dept': dept
    }


def create_test_attribution(test_data, duration_hours=3):
    """Create test attribution"""
    print("\n📋 ÉTAPE 2: Création d'une attribution (durée: 3h)")
    print("=" * 80)
    
    from django.utils import timezone
    from datetime import datetime
    
    now = timezone.now()
    future_date = now + timedelta(hours=duration_hours)
    
    # Create with explicit duree_emprunt and date_attribution 
    attribution = Attribution(
        materiel=test_data['materiel'],
        client=test_data['client'],
        departement=test_data['dept'],
        employe_responsable=test_data['user'],
        date_attribution=now,  # Set explicitly
        date_retour_prevue=future_date.date(),
        heure_retour_prevue=future_date.time(),
        motif='TEST WHATSAPP - Test attribution',
        duree_emprunt=Attribution.DUREE_COURT_TERME
    )
    attribution.save()
    
    print("✓ Attribution créée:")
    print(f"  - ID: {attribution.id}")
    print(f"  - Matériel: {attribution.materiel.nom}")
    print(f"  - Client: {attribution.client.nom}")
    print(f"  - Retour prévu: {attribution.date_retour_prevue} à {attribution.heure_retour_prevue}")
    
    return attribution


def send_creation_notification(attribution, phone_number):
    """Send creation notification"""
    print(f"\n📧 ÉTAPE 3: Envoi notification CRÉATION")
    print("=" * 80)
    
    notification = NotificationLog.objects.create(
        attribution=attribution,
        type_notification=NotificationLog.TYPE_CREATION,
        canal=NotificationLog.CANAL_WHATSAPP,
        destinataire=phone_number,
        duree_emprunt=attribution.duree_emprunt
    )
    
    print(f"✓ Notification créée (ID: {notification.id})")
    print(f"  - Type: CRÉATION")
    print(f"  - Canal: WhatsApp")
    print(f"  - Destinataire: {phone_number}")
    
    # Try to send
    try:
        success = WhatsAppNotificationService.send_notification(notification)
        
        if success:
            print(f"\n✅ Message WhatsApp envoyé!")
            print(f"  - Status: {notification.statut}")
            print(f"  - Date d'envoi: {notification.date_envoi}")
            print(f"  - SID Twilio: {getattr(notification, 'twilio_message_sid', 'N/A')}")
            return True
        else:
            print(f"\n❌ Échec d'envoi du message")
            print(f"  - Erreur: {notification.erreur_message}")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception lors de l'envoi: {str(e)}")
        return False


def send_reminder_notification(attribution, phone_number):
    """Send reminder notification (2h before)"""
    print(f"\n📧 ÉTAPE 4: Envoi notification RAPPEL (2h avant)")
    print("=" * 80)
    
    notification = NotificationLog.objects.create(
        attribution=attribution,
        type_notification=NotificationLog.TYPE_RAPPEL_2H,
        canal=NotificationLog.CANAL_WHATSAPP,
        destinataire=phone_number,
        duree_emprunt=attribution.duree_emprunt
    )
    
    print(f"✓ Notification créée (ID: {notification.id})")
    print(f"  - Type: RAPPEL_2H")
    print(f"  - Canal: WhatsApp")
    print(f"  - Destinataire: {phone_number}")
    
    # Try to send
    try:
        success = WhatsAppNotificationService.send_notification(notification)
        
        if success:
            print(f"\n✅ Message WhatsApp envoyé!")
            print(f"  - Status: {notification.statut}")
            print(f"  - Date d'envoi: {notification.date_envoi}")
            return True
        else:
            print(f"\n❌ Échec d'envoi du message")
            print(f"  - Erreur: {notification.erreur_message}")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception lors de l'envoi: {str(e)}")
        return False


def display_results(phone_number):
    """Display test results"""
    print("\n" + "=" * 80)
    print("✅ TEST TERMINÉ!")
    print("=" * 80)
    
    notifications = NotificationLog.objects.filter(
        destinataire=phone_number,
        attribution__raison__startswith='TEST WHATSAPP'
    ).order_by('-date_creation')
    
    print(f"\n📊 RÉSUMÉ DES NOTIFICATIONS")
    print("-" * 80)
    print(f"Numéro cible: {phone_number}")
    print(f"Total notifications: {notifications.count()}")
    
    for i, notif in enumerate(notifications, 1):
        print(f"\n{i}. {notif.get_type_notification_display()}")
        print(f"   Status: {notif.get_statut_display()}")
        print(f"   Canal: {notif.get_canal_display()}")
        print(f"   Date création: {notif.date_creation}")
        print(f"   Date envoi: {notif.date_envoi}")
        if notif.erreur_message:
            print(f"   Erreur: {notif.erreur_message}")
    
    print(f"\n" + "=" * 80)
    print(f"🔔 Vérifiez votre WhatsApp sur {phone_number}")
    print(f"   Vous devriez avoir reçu {notifications.count()} messages")
    print(f"=" * 80)


def main():
    """Main test function"""
    phone_number = '+24165339274'
    
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " TEST WHATSAPP ATTRIBUTION - RADGESTMAT ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Verify Twilio configuration
    print("\n🔍 VÉRIFICATION CONFIGURATION TWILIO")
    print("=" * 80)
    
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    whatsapp_from = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)
    
    if not account_sid or not auth_token:
        print("❌ Configuration Twilio manquante!")
        print("   Vérifiez settings/development.py")
        return False
    
    print(f"✓ Account SID: {account_sid[:10]}...{account_sid[-10:]}")
    print(f"✓ Auth Token: {'*' * 20}")
    print(f"✓ WhatsApp From: {whatsapp_from}")
    
    try:
        # Setup test data
        test_data = setup_test_data()
        
        # Create attribution
        attribution = create_test_attribution(test_data, duration_hours=3)
        
        # Send creation notification
        creation_success = send_creation_notification(attribution, phone_number)
        
        # Send reminder notification
        reminder_success = send_reminder_notification(attribution, phone_number)
        
        # Display results
        display_results(phone_number)
        
        if creation_success or reminder_success:
            print(f"\n✅ TEST RÉUSSI!")
            print(f"\n💡 Si vous ne recevez pas les messages:")
            print(f"   1. Vérifiez que vous avez rejoint le WhatsApp Sandbox")
            print(f"   2. Envoyez 'join <code>' à +1 415 523 8886")
            print(f"   3. Attendez la confirmation")
            print(f"   4. Relancez ce test")
            return True
        else:
            print(f"\n❌ ÉCHEC - Aucun message n'a pu être envoyé")
            return False
        
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    main()
