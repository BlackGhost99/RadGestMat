"""
Test script for WhatsApp notification system
Validates WhatsApp integration with Twilio
"""
import os
import sys
import django
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'radgestmat.settings')
sys.path.insert(0, os.path.dirname(__file__))

django.setup()

from django.utils import timezone
from users.models import User, Departement
from assets.models import (
    Materiel, Client, Attribution, NotificationLog,
    CategorieMateriels
)
from assets.whatsapp_service import WhatsAppNotificationService
from assets.whatsapp_templates import WhatsAppTemplates


def test_whatsapp_service():
    """
    Complete test of WhatsApp notification system
    """
    print("\n" + "="*70)
    print("🔔 RADGESTMAT WHATSAPP NOTIFICATION SYSTEM TEST")
    print("="*70)
    
    # STAGE 1: Verify Twilio Configuration
    print("\n📋 STAGE 1: Verifying Twilio Configuration...")
    print("-" * 70)
    
    from django.conf import settings
    
    twilio_configured = all([
        hasattr(settings, 'TWILIO_ACCOUNT_SID') and settings.TWILIO_ACCOUNT_SID,
        hasattr(settings, 'TWILIO_AUTH_TOKEN') and settings.TWILIO_AUTH_TOKEN,
        hasattr(settings, 'TWILIO_WHATSAPP_FROM') and settings.TWILIO_WHATSAPP_FROM,
    ])
    
    if not twilio_configured:
        print("❌ TWILIO NOT CONFIGURED!")
        print("\nAdd these settings to radgestmat/settings/development.py:")
        print("""
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_WHATSAPP_FROM = 'whatsapp_business_number'
""")
        return
    
    print("✅ Twilio credentials configured")
    print(f"   Account SID: {settings.TWILIO_ACCOUNT_SID[:10]}...")
    print(f"   WhatsApp From: {settings.TWILIO_WHATSAPP_FROM}")
    
    # STAGE 2: Test Message Templates
    print("\n📋 STAGE 2: Testing Message Templates...")
    print("-" * 70)
    
    templates = WhatsAppTemplates()
    
    # Create mock data for template testing
    class MockMaterial:
        nom = "Perceuse Bosch"
        code = "PERC-001"
    
    class MockClient:
        name = "Dupont"
        first_name = "Jean"
    
    class MockAttribution:
        date_retour_prevue = (timezone.now() + timedelta(days=1)).date()
        heure_retour_prevue = "18:00"
        heure_retour_effective = None
    
    test_cases = [
        ("creation", templates.creation),
        ("rappel_2h", templates.rappel_2h),
        ("rappel_j2", templates.rappel_j2),
        ("rappel_j1", templates.rappel_j1),
        ("rappel_final", templates.rappel_final),
        ("retard", templates.retard),
        ("restitution", templates.restitution),
    ]
    
    for name, template_func in test_cases:
        try:
            message = template_func(
                attribution=MockAttribution(),
                materiel=MockMaterial(),
                client=MockClient(),
                duree_emprunt='LONG'
            )
            print(f"✅ {name:20} - {len(message):4} chars")
        except Exception as e:
            print(f"❌ {name:20} - Error: {e}")
    
    # STAGE 3: Create Test Data
    print("\n📋 STAGE 3: Creating Test Data...")
    print("-" * 70)
    
    # Get or create department
    departement, created = Departement.objects.get_or_create(
        code='TEST',
        defaults={'nom': 'Test Department', 'description': 'For testing'}
    )
    print(f"{'✅ Created' if created else '✓ Found'} Department: {departement.nom}")
    
    # Get or create user
    user, created = User.objects.get_or_create(
        username='whatsapp_test',
        defaults={
            'email': 'test@radgestmat.local',
            'first_name': 'Test',
            'last_name': 'User',
            'departement': departement
        }
    )
    print(f"{'✅ Created' if created else '✓ Found'} User: {user.get_full_name()}")
    
    # Get or create client with phone
    client, created = Client.objects.get_or_create(
        name='TestClient',
        defaults={
            'email': 'testclient@example.com',
            'phone': '+33600000000',  # Test phone
            'responsable': user,
            'departement': departement
        }
    )
    print(f"{'✅ Created' if created else '✓ Found'} Client: {client.name}")
    
    # Get or create category
    category, created = CategorieMateriels.objects.get_or_create(
        code='TEST',
        defaults={'nom': 'Test Category'}
    )
    print(f"{'✅ Created' if created else '✓ Found'} Category: {category.nom}")
    
    # Get or create material
    materiel, created = Materiel.objects.get_or_create(
        code='WHATSAPP-TEST-001',
        defaults={
            'nom': 'Test Material for WhatsApp',
            'categorie': category,
            'description': 'Used for WhatsApp notification testing',
            'quantite': 1
        }
    )
    print(f"{'✅ Created' if created else '✓ Found'} Material: {materiel.nom}")
    
    # STAGE 4: Create Attribution and Test Message
    print("\n📋 STAGE 4: Creating Test Attribution...")
    print("-" * 70)
    
    now = timezone.now()
    attribution = Attribution.objects.create(
        materiel=materiel,
        client=client,
        date_emprunt=now.date(),
        heure_emprunt=now.time(),
        date_retour_prevue=now.date() + timedelta(hours=3),
        heure_retour_prevue=now.time() + timedelta(hours=3),
        departement=departement,
        utilisateur_attribution=user,
        raison='Testing WhatsApp notifications'
    )
    print(f"✅ Created Attribution: {attribution.id}")
    print(f"   Material: {attribution.materiel.nom}")
    print(f"   Client: {attribution.client.name}")
    print(f"   Loan Type: {attribution.duree_emprunt}")
    
    # STAGE 5: Test Sending Notifications
    print("\n📋 STAGE 5: Testing WhatsApp Notifications...")
    print("-" * 70)
    
    notification_types = [
        (NotificationLog.TYPE_CREATION, "Création"),
        (NotificationLog.TYPE_RAPPEL_2H, "Rappel 2h"),
        (NotificationLog.TYPE_RETARD, "Retard"),
        (NotificationLog.TYPE_RESTITUTION, "Restitution"),
    ]
    
    sent_count = 0
    failed_count = 0
    
    for notif_type, notif_name in notification_types:
        print(f"\n  Testing {notif_name}...")
        
        # Create notification log
        notification = NotificationLog.objects.create(
            attribution=attribution,
            type_notification=notif_type,
            canal=NotificationLog.CANAL_WHATSAPP,
            duree_emprunt=attribution.duree_emprunt,
            destinataire=client.phone,
            statut=NotificationLog.STATUT_EN_ATTENTE,
        )
        print(f"    → Created notification log: {notification.id}")
        
        # Try to send
        try:
            result = WhatsAppNotificationService.send_notification(notification)
            
            # Refresh notification from DB
            notification.refresh_from_db()
            
            if result and notification.statut == NotificationLog.STATUT_ENVOYEE:
                print("    ✅ Message sent successfully")
                sent_count += 1
            else:
                print(f"    ❌ Message failed: {notification.statut}")
                if notification.erreur_message:
                    print(f"       Error: {notification.erreur_message}")
                failed_count += 1
        except Exception as e:
            print(f"    ❌ Exception: {e}")
            failed_count += 1
    
    # STAGE 6: Display Statistics
    print("\n📋 STAGE 6: Test Statistics")
    print("-" * 70)
    
    total_notifications = NotificationLog.objects.filter(attribution=attribution).count()
    
    print(f"Total notifications created: {total_notifications}")
    print(f"Successfully sent: {sent_count}")
    print(f"Failed to send: {failed_count}")
    
    print("\n" + "="*70)
    print("✅ WhatsApp notification system test completed!")
    print("="*70 + "\n")


if __name__ == '__main__':
    try:
        test_whatsapp_service()
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
