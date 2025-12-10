"""
Script de test RÉEL pour WhatsApp notifications
Envoie une vraie notification au numéro +241 62308363

PRÉREQUIS:
1. Compte Twilio créé (https://www.twilio.com)
2. WhatsApp Sandbox activé OU numéro Business approuvé
3. Credentials configurés dans settings.py
"""
import os
import sys
import django
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'radgestmat.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
django.setup()

from django.utils import timezone
from users.models import User, Departement
from assets.models import (
    Materiel, Client, Attribution, NotificationLog,
    CategorieMateriels
)
from assets.whatsapp_service import WhatsAppNotificationService


def test_real_whatsapp():
    """
    Test avec le vrai numéro WhatsApp gabonais: +241 62308363
    """
    print("\n" + "="*80)
    print("🔔 TEST RÉEL WHATSAPP - NOTIFICATION RADGESTMAT")
    print("="*80)
    
    # Numéro WhatsApp du Gabon
    PHONE_NUMBER = '+24162308363'
    
    print(f"\n📱 Numéro cible: {PHONE_NUMBER}")
    print("-" * 80)
    
    # ÉTAPE 1: Vérifier la configuration Twilio
    print("\n📋 ÉTAPE 1: Vérification Configuration Twilio")
    print("-" * 80)
    
    from django.conf import settings
    
    has_sid = hasattr(settings, 'TWILIO_ACCOUNT_SID') and settings.TWILIO_ACCOUNT_SID
    has_token = hasattr(settings, 'TWILIO_AUTH_TOKEN') and settings.TWILIO_AUTH_TOKEN
    has_from = hasattr(settings, 'TWILIO_WHATSAPP_FROM') and settings.TWILIO_WHATSAPP_FROM
    
    if not has_sid:
        print("❌ TWILIO_ACCOUNT_SID non configuré!")
        print("\n⚠️  CONFIGURATION REQUISE:")
        print("-" * 80)
        print("Ajoutez dans radgestmat/settings/development.py:\n")
        print("# Twilio WhatsApp Configuration")
        print("TWILIO_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxx'")
        print("TWILIO_AUTH_TOKEN = 'your_auth_token_here'")
        print("TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'  # Sandbox number")
        print("\n📝 Pour obtenir ces credentials:")
        print("1. Allez sur https://www.twilio.com/console")
        print("2. Créez un compte gratuit")
        print("3. Activez WhatsApp Sandbox: https://www.twilio.com/console/sms/whatsapp/sandbox")
        print("4. Envoyez 'join <code>' au numéro sandbox depuis votre WhatsApp")
        print("5. Copiez Account SID et Auth Token dans settings.py")
        print("\n" + "="*80)
        return
    
    if not has_token:
        print("❌ TWILIO_AUTH_TOKEN non configuré!")
        return
    
    if not has_from:
        print("❌ TWILIO_WHATSAPP_FROM non configuré!")
        return
    
    print("✅ Configuration Twilio trouvée")
    print(f"   Account SID: {settings.TWILIO_ACCOUNT_SID[:10]}...")
    print(f"   WhatsApp From: {settings.TWILIO_WHATSAPP_FROM}")
    
    # ÉTAPE 2: Créer ou récupérer les données de test
    print("\n📋 ÉTAPE 2: Création des données de test")
    print("-" * 80)
    
    # Département
    departement, created = Departement.objects.get_or_create(
        code='INFO',
        defaults={
            'nom': 'Département Informatique',
            'description': 'Service informatique'
        }
    )
    print(f"{'✅ Créé' if created else '✓ Trouvé'} Département: {departement.nom}")
    
    # Utilisateur (qui crée l'attribution)
    user, created = User.objects.get_or_create(
        username='admin_test',
        defaults={
            'email': 'admin@radgestmat.ga',
            'first_name': 'Admin',
            'last_name': 'RadGestMat',
            'departement': departement,
            'phone': PHONE_NUMBER  # Même numéro pour le test
        }
    )
    if created:
        user.set_password('test123')
        user.save()
    print(f"{'✅ Créé' if created else '✓ Trouvé'} Utilisateur: {user.get_full_name()}")
    
    # Client (qui reçoit le matériel)
    client, created = Client.objects.get_or_create(
        name='Client Test Gabon',
        defaults={
            'email': 'client@example.ga',
            'phone': PHONE_NUMBER,  # Numéro WhatsApp gabonais
            'responsable': user,
            'departement': departement
        }
    )
    # S'assurer que le phone est à jour
    if client.phone != PHONE_NUMBER:
        client.phone = PHONE_NUMBER
        client.save()
    print(f"{'✅ Créé' if created else '✓ Trouvé'} Client: {client.name}")
    print(f"   📱 Phone: {client.phone}")
    
    # Catégorie
    category, created = CategorieMateriels.objects.get_or_create(
        code='ELEC',
        defaults={'nom': 'Électronique'}
    )
    print(f"{'✅ Créé' if created else '✓ Trouvé'} Catégorie: {category.nom}")
    
    # Matériel
    materiel, created = Materiel.objects.get_or_create(
        code='LAPTOP-TEST-001',
        defaults={
            'nom': 'Ordinateur Portable Test',
            'categorie': category,
            'description': 'Laptop pour test WhatsApp',
            'quantite': 1
        }
    )
    print(f"{'✅ Créé' if created else '✓ Trouvé'} Matériel: {materiel.nom}")
    
    # ÉTAPE 3: Créer une Attribution de test
    print("\n📋 ÉTAPE 3: Création d'une Attribution de test")
    print("-" * 80)
    
    now = timezone.now()
    attribution = Attribution.objects.create(
        materiel=materiel,
        client=client,
        date_emprunt=now.date(),
        heure_emprunt=now.time(),
        date_retour_prevue=(now + timedelta(hours=3)).date(),
        heure_retour_prevue=(now + timedelta(hours=3)).time(),
        departement=departement,
        utilisateur_attribution=user,
        raison='Test WhatsApp notification système RadGestMat'
    )
    print(f"✅ Attribution créée: #{attribution.id}")
    print(f"   Matériel: {attribution.materiel.nom}")
    print(f"   Client: {attribution.client.name}")
    print(f"   Type: {attribution.duree_emprunt}")
    print(f"   Retour prévu: {attribution.date_retour_prevue} {attribution.heure_retour_prevue}")
    
    # ÉTAPE 4: Envoyer la notification WhatsApp
    print("\n📋 ÉTAPE 4: Envoi de la notification WhatsApp")
    print("-" * 80)
    print(f"\n📱 Envoi vers: {PHONE_NUMBER}")
    print("⏳ Envoi en cours...\n")
    
    try:
        # Créer le log de notification
        notification = NotificationLog.objects.create(
            attribution=attribution,
            type_notification=NotificationLog.TYPE_CREATION,
            canal=NotificationLog.CANAL_WHATSAPP,
            duree_emprunt=attribution.duree_emprunt,
            destinataire=PHONE_NUMBER,
            statut=NotificationLog.STATUT_EN_ATTENTE,
        )
        
        # Envoyer via WhatsApp
        result = WhatsAppNotificationService.send_notification(notification)
        
        # Rafraîchir le log
        notification.refresh_from_db()
        
        if result and notification.statut == NotificationLog.STATUT_ENVOYEE:
            print("="*80)
            print("🎉 SUCCÈS! Message WhatsApp envoyé!")
            print("="*80)
            print(f"\n✅ Status: {notification.statut}")
            print(f"✅ Date d'envoi: {notification.date_envoi}")
            print(f"✅ Notification ID: {notification.id}")
            print(f"\n📱 Vérifiez votre WhatsApp ({PHONE_NUMBER})")
            print("   Vous devriez recevoir un message dans quelques secondes!")
            print("\n💬 Message envoyé:")
            print("-" * 80)
            print("✅ Emprunt Confirmé")
            print(f"\nBonjour {client.name}!")
            print(f"\nVotre demande d'emprunt a été confirmée:")
            print(f"\n📦 Matériel: {materiel.nom}")
            print(f"🏷️ Référence: {materiel.code}")
            print(f"📅 Date retour: {attribution.date_retour_prevue}")
            print(f"🕐 Heure retour: {attribution.heure_retour_prevue}")
            print("-" * 80)
        else:
            print("="*80)
            print("❌ ÉCHEC de l'envoi")
            print("="*80)
            print(f"\n❌ Status: {notification.statut}")
            if notification.erreur_message:
                print(f"❌ Erreur: {notification.erreur_message}")
            
            print("\n💡 CAUSES POSSIBLES:")
            print("-" * 80)
            print("1. WhatsApp Sandbox non activé")
            print("   → Allez sur https://www.twilio.com/console/sms/whatsapp/sandbox")
            print(f"   → Envoyez 'join <code>' au numéro sandbox depuis {PHONE_NUMBER}")
            print("\n2. Credentials Twilio incorrects")
            print("   → Vérifiez TWILIO_ACCOUNT_SID et TWILIO_AUTH_TOKEN")
            print("\n3. Numéro WhatsApp non vérifié")
            print("   → Le numéro doit être connecté au sandbox Twilio")
            
    except Exception as e:
        print("="*80)
        print("❌ ERREUR lors de l'envoi")
        print("="*80)
        print(f"\n❌ Exception: {str(e)}")
        print("\n💡 Vérifiez:")
        print("- Connexion internet active")
        print("- Credentials Twilio valides")
        print("- WhatsApp Sandbox activé")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ Test terminé")
    print("="*80)
    print("\n📊 Résumé:")
    print(f"   Attribution ID: {attribution.id}")
    print(f"   Client: {client.name}")
    print(f"   Phone: {client.phone}")
    print(f"   Notification ID: {notification.id if 'notification' in locals() else 'N/A'}")
    
    # Afficher les logs de notification
    all_notifications = NotificationLog.objects.filter(attribution=attribution)
    print(f"\n📝 Notifications créées pour cette attribution: {all_notifications.count()}")
    for notif in all_notifications:
        print(f"   - {notif.get_type_notification_display()} ({notif.get_canal_display()}): {notif.statut}")


if __name__ == '__main__':
    try:
        test_real_whatsapp()
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
