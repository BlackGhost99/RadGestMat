#!/usr/bin/env python
"""
Script de test pour vérifier l'envoi des notifications Email et WhatsApp
lors d'une attribution par l'utilisateur Brice.

Utilisateur: Brice
Email: helpdesk.libreville@radissonblu.com
WhatsApp: +241 05 33 92 74
"""
import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# Configuration Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'radgestmat.settings')
django.setup()

from django.contrib.auth import get_user_model
from assets.models import (
    Materiel, Client, Attribution, Departement, Categorie,
    NotificationPreferences, NotificationLog
)
from assets.email_service import NotificationEmailService
from assets.whatsapp_service import WhatsAppNotificationService

User = get_user_model()


def normalize_phone(phone):
    """Normalise le numéro de téléphone"""
    if not phone:
        return None
    # Enlever les espaces
    phone = phone.replace(' ', '').replace('-', '')
    # S'assurer qu'il commence par +
    if not phone.startswith('+'):
        phone = '+' + phone
    return phone


def main():
    print("=" * 80)
    print("TEST D'ATTRIBUTION AVEC NOTIFICATIONS EMAIL ET WHATSAPP")
    print("=" * 80)
    print("\nUtilisateur: Brice")
    print("Email: helpdesk.libreville@radissonblu.com")
    print("WhatsApp: +241 05 33 92 74")
    print("=" * 80)
    
    # ========================================
    # 1. PRÉPARATION DES DONNÉES
    # ========================================
    print("\nETAPE 1: Preparation des donnees")
    print("-" * 80)
    
    # Trouver ou créer l'utilisateur Brice
    try:
        # Chercher d'abord par username
        user = User.objects.filter(username='brice').first()
        if not user:
            # Chercher par email
            user = User.objects.filter(email='helpdesk.libreville@radissonblu.com').first()
        
        if not user:
            # Créer un nouvel utilisateur
            user = User.objects.create(
                username='brice',
                email='helpdesk.libreville@radissonblu.com',
                first_name='Brice',
                last_name='Moukabi Ngwa',
            )
            user.set_password('test123')
            user.save()
            created = True
        else:
            created = False
        if created:
            user.set_password('test123')
            user.save()
            print(f"[OK] Utilisateur cree: {user.get_full_name()} ({user.email})")
        else:
            print(f"[OK] Utilisateur trouve: {user.get_full_name()} ({user.email})")
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la creation/recuperation de l'utilisateur: {e}")
        return
    
    # Trouver un département existant
    departement = Departement.objects.first()
    if not departement:
        print("❌ Aucun département trouvé. Veuillez créer un département d'abord.")
        return
        print(f"[OK] Departement: {departement.nom}")
    
    # Trouver un matériel disponible existant
    materiel = Materiel.objects.filter(
        statut_disponibilite=Materiel.STATUT_DISPONIBLE,
        departement=departement
    ).first()
    
    if not materiel:
        print("[WARN] Aucun materiel disponible trouve. Recherche d'un materiel quelconque...")
        materiel = Materiel.objects.filter(departement=departement).first()
    
    if not materiel:
        print("[INFO] Aucun materiel trouve. Creation d'un materiel de test...")
        # Créer une catégorie si elle n'existe pas
        categorie, _ = Categorie.objects.get_or_create(
            nom='Test',
            departement=departement,
            defaults={'description': 'Categorie de test'}
        )
        
        # Créer un matériel de test
        materiel = Materiel.objects.create(
            nom='Ordinateur Portable Test',
            categorie=categorie,
            departement=departement,
            etat_technique=Materiel.ETAT_FONCTIONNEL,
            statut_disponibilite=Materiel.STATUT_DISPONIBLE,
            description='Materiel de test pour attribution'
        )
        print(f"[OK] Materiel de test cree: {materiel.nom} ({materiel.asset_id})")
    else:
        print(f"[OK] Materiel: {materiel.nom} ({materiel.asset_id})")
    
    # Trouver ou créer un client avec le numéro WhatsApp
    phone_whatsapp = normalize_phone("+241 05 33 92 74")
    client_email = "helpdesk.libreville@radissonblu.com"
    
    try:
        # Chercher d'abord par email
        client = Client.objects.filter(email=client_email).first()
        if not client:
            # Chercher par téléphone
            client = Client.objects.filter(telephone__icontains="05339274").first()
        
        if not client:
            # Créer un nouveau client
            client = Client.objects.create(
                nom="Brice Moukabi Ngwa",
                type_client=Client.TYPE_INTERNE,
                email=client_email,
                telephone=phone_whatsapp,
                departement=departement
            )
            print(f"[OK] Client cree: {client.nom}")
        else:
            # Mettre à jour les informations si nécessaire
            if client.email != client_email:
                client.email = client_email
            if client.telephone != phone_whatsapp:
                client.telephone = phone_whatsapp
            client.save()
            print(f"[OK] Client trouve: {client.nom}")
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la creation/recuperation du client: {e}")
        return
    
    print(f"   Email: {client.email}")
    print(f"   Téléphone: {client.telephone}")
    
    # ========================================
    # 2. CONFIGURATION DES PRÉFÉRENCES DE NOTIFICATION
    # ========================================
    print("\nETAPE 2: Configuration des preferences de notification")
    print("-" * 80)
    
    try:
        preferences, created = NotificationPreferences.objects.get_or_create(
            client=client,
            defaults={
                'notifications_email': True,
                'notifications_whatsapp': True,
                'phone_number': phone_whatsapp,
            }
        )
        
        if not created:
            # Mettre à jour les préférences
            preferences.notifications_email = True
            preferences.notifications_whatsapp = True
            preferences.phone_number = phone_whatsapp
            preferences.save()
            print("[OK] Preferences mises a jour")
        else:
            print("[OK] Preferences creees")
        
        print(f"   Email activé: {preferences.notifications_email}")
        print(f"   WhatsApp activé: {preferences.notifications_whatsapp}")
        print(f"   Numéro WhatsApp: {preferences.phone_number}")
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la configuration des preferences: {e}")
        return
    
    # ========================================
    # 3. CRÉATION DE L'ATTRIBUTION
    # ========================================
    print("\nETAPE 3: Creation de l'attribution")
    print("-" * 80)
    
    try:
        # Calculer la date de retour (dans 3 jours pour un test long terme)
        date_retour = timezone.now().date() + timedelta(days=3)
        
        # Créer l'attribution
        attribution = Attribution.objects.create(
            materiel=materiel,
            client=client,
            employe_responsable=user,
            departement=departement,
            date_retour_prevue=date_retour,
            motif="Test d'attribution avec notifications",
            notes="Test automatique pour vérifier l'envoi des notifications Email et WhatsApp"
        )
        
        # Calculer automatiquement la durée d'emprunt
        attribution.duree_emprunt = attribution.calculate_duree_emprunt()
        attribution.save()
        
        print(f"[OK] Attribution creee: ID {attribution.id}")
        print(f"   Matériel: {attribution.materiel.nom} ({attribution.materiel.asset_id})")
        print(f"   Client: {attribution.client.nom}")
        print(f"   Responsable: {attribution.employe_responsable.get_full_name()}")
        print(f"   Date retour prévue: {attribution.date_retour_prevue}")
        print(f"   Durée emprunt: {attribution.get_duree_emprunt_display()}")
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la creation de l'attribution: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ========================================
    # 4. VÉRIFICATION DES NOTIFICATIONS ENVOYÉES
    # ========================================
    print("\nETAPE 4: Verification des notifications")
    print("-" * 80)
    
    # Attendre un peu pour que les signaux se déclenchent
    import time
    time.sleep(2)
    
    # Vérifier les logs de notification
    notifications = NotificationLog.objects.filter(
        attribution=attribution,
        type_notification=NotificationLog.TYPE_CREATION
    ).order_by('-id')
    
    print(f"\nNotifications creees: {notifications.count()}")
    
    email_notif = notifications.filter(canal=NotificationLog.CANAL_EMAIL).first()
    whatsapp_notif = notifications.filter(canal=NotificationLog.CANAL_WHATSAPP).first()
    
    # Vérifier l'email
    if email_notif:
        print(f"\nNotification Email:")
        print(f"   ID: {email_notif.id}")
        print(f"   Destinataire: {email_notif.destinataire}")
        print(f"   Statut: {email_notif.get_statut_display()}")
        if email_notif.erreur_message:
            print(f"   [WARN] Erreur: {email_notif.erreur_message}")
        else:
            print(f"   [OK] Email envoye avec succes")
    else:
        print(f"\n[WARN] Aucune notification email trouvee")
    
    # Vérifier WhatsApp
    if whatsapp_notif:
        print(f"\nNotification WhatsApp:")
        print(f"   ID: {whatsapp_notif.id}")
        print(f"   Destinataire: {whatsapp_notif.destinataire}")
        print(f"   Statut: {whatsapp_notif.get_statut_display()}")
        if whatsapp_notif.erreur_message:
            print(f"   [WARN] Erreur: {whatsapp_notif.erreur_message}")
        else:
            print(f"   [OK] WhatsApp envoye avec succes")
    else:
        print(f"\n[WARN] Aucune notification WhatsApp trouvee")
    
    # ========================================
    # 5. RÉSUMÉ
    # ========================================
    print("\n" + "=" * 80)
    print("RESUME DU TEST")
    print("=" * 80)
    print(f"[OK] Attribution creee: ID {attribution.id}")
    print(f"[OK] Notifications Email: {'Oui' if email_notif and email_notif.statut == NotificationLog.STATUT_ENVOYEE else 'Non/Erreur'}")
    print(f"[OK] Notifications WhatsApp: {'Oui' if whatsapp_notif and whatsapp_notif.statut == NotificationLog.STATUT_ENVOYEE else 'Non/Erreur'}")
    
    if email_notif and email_notif.statut != NotificationLog.STATUT_ENVOYEE:
        print(f"\n[WARN] Email non envoye. Verifiez:")
        print(f"   - Configuration SMTP dans settings.py")
        print(f"   - DEFAULT_FROM_EMAIL configure")
        print(f"   - Serveur SMTP accessible")
    
    if whatsapp_notif and whatsapp_notif.statut != NotificationLog.STATUT_ENVOYEE:
        print(f"\n[WARN] WhatsApp non envoye. Verifiez:")
        print(f"   - TWILIO_ACCOUNT_SID configure dans settings.py")
        print(f"   - TWILIO_AUTH_TOKEN configure dans settings.py")
        print(f"   - TWILIO_WHATSAPP_FROM configure dans settings.py")
        print(f"   - Numero WhatsApp valide et formate correctement")
    
    print("\n" + "=" * 80)
    print("[OK] Test termine!")
    print("=" * 80)


if __name__ == '__main__':
    main()
