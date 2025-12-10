#!/usr/bin/env python
"""
Script de test pour les notifications par email
Test manuel des emails avant déploiement
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'radgestmat.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from assets.models import (
    Departement, Materiel, Client, Attribution, 
    NotificationLog, NotificationPreferences
)
from assets.email_service import NotificationEmailService
from django.utils import timezone
from datetime import datetime, timedelta
import time


def test_email_service():
    """Test complet du service d'email"""
    
    print("=" * 80)
    print("TEST DU SERVICE D'EMAIL - NOTIFICATIONS MATÉRIEL")
    print("=" * 80)
    print()
    
    # 1. Vérifier les données de test
    print("📋 Étape 1: Vérification des données de test...")
    print("-" * 80)
    
    try:
        dept = Departement.objects.first() or Departement.objects.create(
            nom="TEST", code="TST"
        )
        print(f"✓ Département: {dept.nom}")
    except Exception as e:
        print(f"✗ Erreur département: {e}")
        return
    
    try:
        user = User.objects.filter(email__isnull=False, email__gt='').first()
        if not user:
            user = User.objects.create_user(
                username='test_user',
                email='test@example.com',
                first_name='Test',
                last_name='User'
            )
        print(f"✓ Utilisateur: {user.username} ({user.email})")
    except Exception as e:
        print(f"✗ Erreur utilisateur: {e}")
        return
    
    try:
        materiel = Materiel.objects.filter(departement=dept).first() or Materiel.objects.create(
            nom="Projecteur Test",
            numero_inventaire="TEST-001",
            asset_id="PROJ-TEST-001",
            departement=dept,
            etat_technique="FONCTIONNEL",
            statut_disponibilite="DISPONIBLE"
        )
        print(f"✓ Matériel: {materiel.nom} ({materiel.asset_id})")
    except Exception as e:
        print(f"✗ Erreur matériel: {e}")
        return
    
    try:
        client = Client.objects.filter(departement=dept).first() or Client.objects.create(
            nom="Client Test",
            type_client="HEBERGEMENT",
            email=user.email,
            departement=dept
        )
        print(f"✓ Client: {client.nom}")
    except Exception as e:
        print(f"✗ Erreur client: {e}")
        return
    
    print()
    
    # 2. Créer une attribution de test
    print("📋 Étape 2: Création d'une attribution de test...")
    print("-" * 80)
    
    try:
        # Attribution court-terme (3h)
        date_start = timezone.now()
        date_end = date_start + timedelta(hours=3)
        
        attribution = Attribution.objects.create(
            materiel=materiel,
            client=client,
            departement=dept,
            employe_responsable=user,
            date_retour_prevue=date_end.date(),
            heure_retour_prevue=date_end.time(),
            motif="Test"
        )
        print(f"✓ Attribution créée: {attribution.id}")
        print(f"  - Durée: {attribution.duree_emprunt}")
        print(f"  - Retour: {attribution.date_retour_prevue} à {attribution.heure_retour_prevue}")
    except Exception as e:
        print(f"✗ Erreur création attribution: {e}")
        return
    
    print()
    
    # 3. Créer les préférences de notification
    print("📋 Étape 3: Création des préférences de notification...")
    print("-" * 80)
    
    try:
        NotificationPreferences.objects.filter(user=user).delete()
        prefs = NotificationPreferences.objects.create(
            user=user,
            notifications_email=True,
            notifications_whatsapp=False,
            rappel_j_moins_2=True,
            rappel_j_moins_1=True,
            rappel_final=True,
            rappel_2h_avant=True
        )
        print(f"✓ Préférences créées pour {user.username}")
        print(f"  - Email: {prefs.notifications_email}")
        print(f"  - WhatsApp: {prefs.notifications_whatsapp}")
    except Exception as e:
        print(f"✗ Erreur préférences: {e}")
        return
    
    print()
    
    # 4. Tester l'envoi d'emails
    print("📋 Étape 4: Test d'envoi des notifications...")
    print("-" * 80)
    
    test_cases = [
        ("CREATION", NotificationLog.TYPE_CREATION),
        ("RAPPEL_2H", NotificationLog.TYPE_RAPPEL_2H),
        ("RETARD", NotificationLog.TYPE_RETARD),
        ("RESTITUTION", NotificationLog.TYPE_RESTITUTION),
    ]
    
    for label, type_notif in test_cases:
        try:
            print(f"\n  📧 Test {label}:")
            result = NotificationEmailService.send_reminder_notification(
                attribution=attribution,
                type_rappel=type_notif,
                destinataire_email=user.email
            )
            
            if result:
                print(f"     ✓ Email envoyé avec succès")
                # Vérifier le log
                log = NotificationLog.objects.filter(
                    attribution=attribution,
                    type_notification=type_notif
                ).last()
                print(f"     ✓ Log créé: {log.id} - Status: {log.statut}")
            else:
                print(f"     ✗ Erreur lors de l'envoi")
            
            time.sleep(1)  # Attendre 1 seconde entre les envois
            
        except Exception as e:
            print(f"     ✗ Exception: {e}")
    
    print()
    
    # 5. Afficher les stats
    print("📋 Étape 5: Statistiques...")
    print("-" * 80)
    
    logs = NotificationLog.objects.filter(attribution=attribution)
    print(f"Total notifications créées: {logs.count()}")
    print(f"Envoyées avec succès: {logs.filter(statut=NotificationLog.STATUT_ENVOYEE).count()}")
    print(f"En erreur: {logs.filter(statut=NotificationLog.STATUT_ECHEC).count()}")
    
    print()
    print("=" * 80)
    print("✓ TEST TERMINÉ")
    print("=" * 80)
    
    print("\n📌 Prochaines étapes:")
    print("1. Vérifier les emails reçus")
    print("2. Tester avec des vraies adresses email")
    print("3. Configurer APScheduler pour les rappels planifiés")
    print("4. Implémenter WhatsApp (Twilio)")


if __name__ == '__main__':
    try:
        test_email_service()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
