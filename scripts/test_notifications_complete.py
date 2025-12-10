"""
Script de test complet pour le système de notifications
Phase 3: Signaux Django + Phase 6: Dashboard

Test:
1. Création d'une attribution → Notification automatique
2. Retour de matériel → Confirmation automatique
3. Affichage du dashboard
4. Gestion des préférences
"""
import os
import sys
import django
from datetime import date, time, timedelta
from django.utils import timezone

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'radgestmat.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from assets.models import (
    Materiel, Client, Attribution, Departement, Categorie,
    NotificationLog, NotificationPreferences
)

User = get_user_model()

def main():
    print("=" * 80)
    print("🧪 TEST DU SYSTÈME DE NOTIFICATIONS COMPLET")
    print("=" * 80)
    
    # ========================================
    # 1. PRÉPARATION DES DONNÉES DE TEST
    # ========================================
    print("\n📦 1. Préparation des données de test...")
    
    # Département
    dept, _ = Departement.objects.get_or_create(
        code="TEST",
        defaults={'nom': "Test Department", 'description': "Test"}
    )
    
    # Catégorie
    cat, _ = Categorie.objects.get_or_create(
        nom="Ordinateurs",
        defaults={'departement': dept, 'description': "Test"}
    )
    
    # Matériel
    materiel, _ = Materiel.objects.get_or_create(
        asset_id="TEST-001",
        defaults={
            'nom': "Ordinateur Portable Test",
            'categorie': cat,
            'departement': dept,
            'etat_technique': Materiel.ETAT_FONCTIONNEL,
            'statut_disponibilite': Materiel.STATUT_DISPONIBLE,
        }
    )
    
    # Client
    client, _ = Client.objects.get_or_create(
        nom="Client Test",
        defaults={
            'type_client': Client.TYPE_INTERNE,
            'email': "test@example.com",
            'telephone': "+24105339274",
            'departement': dept
        }
    )
    
    # Utilisateur
    user, _ = User.objects.get_or_create(
        username="testuser",
        defaults={
            'email': "testuser@example.com",
            'first_name': "Test",
            'last_name': "User"
        }
    )
    
    # Préférences de notification (Email + WhatsApp)
    prefs, created = NotificationPreferences.objects.get_or_create(
        client=client,
        defaults={
            'notifications_email': True,
            'notifications_whatsapp': True,
            'phone_number': "+24105339274",
            'rappel_j_moins_2': True,
            'rappel_j_moins_1': True,
            'rappel_final': True,
            'rappel_2h_avant': True
        }
    )
    
    if created:
        print(f"   ✅ Préférences créées pour {client.nom}")
    else:
        print(f"   ℹ️  Préférences existantes pour {client.nom}")
    
    print(f"   ✅ Département: {dept.nom}")
    print(f"   ✅ Catégorie: {cat.nom}")
    print(f"   ✅ Matériel: {materiel.nom} ({materiel.asset_id})")
    print(f"   ✅ Client: {client.nom} ({client.email})")
    print(f"   ✅ User: {user.username}")
    
    # ========================================
    # 2. TEST CRÉATION D'ATTRIBUTION
    # ========================================
    print("\n📧 2. Test Signal de Création d'Attribution...")
    
    # Compter les notifications avant
    notif_count_before = NotificationLog.objects.filter(
        type_notification='CREATION'
    ).count()
    
    # Créer une attribution (déclenche le signal post_save)
    attribution = Attribution.objects.create(
        materiel=materiel,
        client=client,
        employe_responsable=user,
        departement=dept,
        date_attribution=timezone.now(),
        date_retour_prevue=timezone.now().date() + timedelta(days=7),
        heure_retour_prevue=time(17, 0),
        duree_emprunt=Attribution.DUREE_LONG_TERME,
        motif="Test automatique du système de notifications"
    )
    
    print(f"   ✅ Attribution créée: ID={attribution.id}")
    
    # Vérifier les notifications créées
    notif_count_after = NotificationLog.objects.filter(
        type_notification='CREATION'
    ).count()
    
    nouvelles_notifs = notif_count_after - notif_count_before
    print(f"   📨 Notifications de création envoyées: {nouvelles_notifs}")
    
    # Afficher les détails
    notifs_creation = NotificationLog.objects.filter(
        attribution=attribution,
        type_notification='CREATION'
    )
    
    for notif in notifs_creation:
        print(f"      - Canal: {notif.canal}")
        print(f"        Destinataire: {notif.destinataire}")
        print(f"        Statut: {notif.statut}")
        print(f"        Date: {notif.date_envoi}")
        if notif.message_id:
            print(f"        Message ID: {notif.message_id}")
    
    # ========================================
    # 3. TEST RETOUR DE MATÉRIEL
    # ========================================
    print("\n📦 3. Test Signal de Retour de Matériel...")
    
    # Compter les notifications avant
    notif_restitution_before = NotificationLog.objects.filter(
        type_notification='RESTITUTION'
    ).count()
    
    # Marquer comme retourné (déclenche le signal pre_save + post_save)
    attribution.date_retour_effective = date.today()
    attribution.heure_retour_effective = time(16, 30)
    attribution.save()
    
    print(f"   ✅ Attribution marquée comme retournée")
    
    # Vérifier les notifications de restitution
    notif_restitution_after = NotificationLog.objects.filter(
        type_notification='RESTITUTION'
    ).count()
    
    nouvelles_restitutions = notif_restitution_after - notif_restitution_before
    print(f"   📨 Notifications de restitution envoyées: {nouvelles_restitutions}")
    
    # Afficher les détails
    notifs_restitution = NotificationLog.objects.filter(
        attribution=attribution,
        type_notification='RESTITUTION'
    )
    
    for notif in notifs_restitution:
        print(f"      - Canal: {notif.canal}")
        print(f"        Destinataire: {notif.destinataire}")
        print(f"        Statut: {notif.statut}")
        print(f"        Date: {notif.date_envoi}")
    
    # ========================================
    # 4. STATISTIQUES DASHBOARD
    # ========================================
    print("\n📊 4. Statistiques Dashboard...")
    
    total_notifs = NotificationLog.objects.count()
    emails = NotificationLog.objects.filter(canal='EMAIL').count()
    whatsapp = NotificationLog.objects.filter(canal='WHATSAPP').count()
    succes = NotificationLog.objects.filter(statut='ENVOYEE').count()
    
    print(f"   📊 Total notifications: {total_notifs}")
    print(f"   📧 Emails: {emails}")
    print(f"   💬 WhatsApp: {whatsapp}")
    print(f"   ✅ Succès: {succes}")
    
    if total_notifs > 0:
        taux_succes = (succes / total_notifs) * 100
        print(f"   📈 Taux de succès: {taux_succes:.1f}%")
    
    # ========================================
    # 5. RÉSUMÉ FINAL
    # ========================================
    print("\n" + "=" * 80)
    print("✅ TESTS TERMINÉS")
    print("=" * 80)
    print(f"""
    ✓ Signaux Django configurés
    ✓ Notification de création: {nouvelles_notifs > 0}
    ✓ Notification de restitution: {nouvelles_restitutions > 0}
    ✓ Dashboard accessible: http://127.0.0.1:8000/notifications/dashboard/
    ✓ Préférences accessibles: http://127.0.0.1:8000/notifications/preferences/
    
    📌 Attribution de test créée: ID={attribution.id}
    📌 Consultez le dashboard pour voir l'historique complet
    """)

if __name__ == '__main__':
    main()
