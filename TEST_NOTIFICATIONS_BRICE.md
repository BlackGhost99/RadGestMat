# Test des Notifications Email et WhatsApp

## Résumé du Test

**Date:** 11 janvier 2026  
**Utilisateur testé:** Brice  
**Email:** helpdesk.libreville@radissonblu.com  
**WhatsApp:** +241 05 33 92 74

## ✅ Résultats du Test

### 1. Attribution Créée avec Succès

- **ID Attribution:** 2
- **Matériel:** Ordinateur Portable Test (OKP-000095)
- **Client:** Brice Moukabi Ngwa
- **Responsable:** Brice MOUKABI-NGWA
- **Date retour prévue:** 2026-01-14
- **Durée emprunt:** Long terme (> 24h)

### 2. Notifications Créées

Le système a automatiquement créé **2 notifications** :
- ✅ **Notification Email** (ID: 1)
- ✅ **Notification WhatsApp** (ID: 2)

### 3. Statut des Notifications

#### 📧 Email
- **Statut:** Échec (retry en cours)
- **Destinataire:** helpdesk.libreville@radissonblu.com
- **Problème:** Erreur d'encodage Unicode dans le template HTML
  - Caractère `✓` (checkmark) non supporté par l'encodage Windows cp1252
  - **Solution:** Voir section "Corrections nécessaires" ci-dessous

#### 💬 WhatsApp
- **Statut:** EN_ATTENTE
- **Destinataire:** +24105339274
- **Problème:** Twilio SDK non installé
  - **Solution:** Installer `pip install twilio`

## 🔍 Comment le Système Fonctionne

### Architecture des Notifications

1. **Signal Django** (`assets/signals.py`)
   - Détecte automatiquement la création d'une attribution
   - Déclenche l'envoi des notifications selon les préférences

2. **Préférences de Notification** (`NotificationPreferences`)
   - Email activé par défaut
   - WhatsApp activé si numéro configuré
   - Géré par client/utilisateur

3. **Services de Notification**
   - `NotificationEmailService` : Gestion des emails
   - `WhatsAppNotificationService` : Gestion WhatsApp via Twilio

4. **Logs de Notification** (`NotificationLog`)
   - Traçabilité complète
   - Statuts : EN_ATTENTE, ENVOYEE, ECHEC, ECHEC_PERMANENT
   - Gestion des retry automatiques

## 🧪 Comment Tester

### Script de Test

Un script de test a été créé : `test_attribution_brice.py`

**Utilisation:**
```bash
python test_attribution_brice.py
```

**Ce que fait le script:**
1. Trouve ou crée l'utilisateur Brice
2. Trouve ou crée un matériel disponible
3. Trouve ou crée le client avec email et WhatsApp
4. Configure les préférences de notification (Email + WhatsApp activés)
5. Crée une attribution
6. Vérifie que les notifications sont créées et envoyées

### Test Manuel via Interface Web

1. **Se connecter** avec l'utilisateur Brice
2. **Aller sur** la page d'un matériel disponible
3. **Cliquer sur** "Check-out" (Attribution)
4. **Sélectionner** un client (ou créer un nouveau)
5. **Remplir** les informations (date retour, motif, etc.)
6. **Enregistrer** l'attribution
7. **Vérifier** les notifications dans :
   - Les logs de notification (admin)
   - La boîte email du client
   - WhatsApp du client (si configuré)

## 🔧 Corrections Nécessaires

### 1. Problème d'Encodage Email

**Problème:** Les templates email contiennent des caractères Unicode (emojis) non supportés par Windows cp1252.

**Solution 1: Modifier les templates email**
- Remplacer les emojis par du texte simple
- Ou utiliser des images/icons HTML

**Solution 2: Forcer UTF-8 dans les settings**
```python
# Dans settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# Forcer UTF-8
import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
```

**Fichiers à modifier:**
- `assets/email_service.py` (ligne 198-206) : Sujets avec emojis
- `templates/assets/emails/*.html` : Templates avec emojis

### 2. Installation Twilio SDK

**Problème:** Twilio SDK non installé pour WhatsApp.

**Solution:**
```bash
pip install twilio
```

**Configuration requise dans `settings.py`:**
```python
TWILIO_ACCOUNT_SID = 'Votre_SID'
TWILIO_AUTH_TOKEN = 'Votre_Token'
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'  # Numéro Twilio
```

**Vérification:**
```python
# Test rapide
from twilio.rest import Client
client = Client('ACxxx', 'token')
print("Twilio OK")
```

## 📊 Vérification des Notifications

### Via l'Interface Admin

1. Aller sur `/admin/assets/notificationlog/`
2. Filtrer par attribution ou client
3. Vérifier les statuts :
   - ✅ **ENVOYEE** : Notification envoyée avec succès
   - ⏳ **EN_ATTENTE** : En attente d'envoi
   - ❌ **ECHEC** : Erreur temporaire (retry automatique)
   - 🚫 **ECHEC_PERMANENT** : Erreur permanente (3 tentatives échouées)

### Via les Logs

Les logs sont dans :
- Console (si DEBUG=True)
- Fichier `logs/radgestmat.log`

Rechercher :
- `Nouvelle attribution créée`
- `Email de création envoyé`
- `WhatsApp de création envoyé`
- `Erreur lors de l'envoi`

## ✅ Conclusion

### Ce qui Fonctionne

1. ✅ **Création automatique des notifications** lors d'une attribution
2. ✅ **Gestion des préférences** par client
3. ✅ **Logs complets** pour traçabilité
4. ✅ **Architecture modulaire** (Email et WhatsApp séparés)

### Ce qui Nécessite des Corrections

1. ⚠️ **Encodage Unicode** dans les templates email (Windows)
2. ⚠️ **Installation Twilio SDK** pour WhatsApp

### Prochaines Étapes

1. Corriger l'encodage des templates email
2. Installer Twilio SDK
3. Configurer les credentials Twilio
4. Re-tester avec le script
5. Vérifier la réception réelle des emails et WhatsApp

## 📝 Notes Techniques

### Structure des Notifications

```
Attribution créée
    ↓
Signal post_save déclenché
    ↓
Récupération NotificationPreferences
    ↓
Si Email activé → Créer NotificationLog (EMAIL) → Envoyer
Si WhatsApp activé → Créer NotificationLog (WHATSAPP) → Envoyer
    ↓
Mise à jour statut dans NotificationLog
```

### Types de Notifications

- `TYPE_CREATION` : Attribution créée
- `TYPE_RAPPEL_2H` : Rappel 2h avant retour (moyen terme)
- `TYPE_RAPPEL_J_MOINS_2` : Rappel 2 jours avant
- `TYPE_RAPPEL_J_MOINS_1` : Rappel 1 jour avant
- `TYPE_RAPPEL_FINAL` : Rappel jour du retour
- `TYPE_RETARD` : Matériel en retard
- `TYPE_RESTITUTION` : Matériel restitué

### Canaux

- `CANAL_EMAIL` : Notification par email
- `CANAL_WHATSAPP` : Notification par WhatsApp
