# 🎉 Twilio Configuration - Vos Credentials

**Date:** December 10, 2025  
**Projet:** RadGestMat Notification System  
**Numéro test:** +241 62308363

---

## ✅ Vos Informations Twilio

Voici ce que vous avez reçu de Twilio:

### 1. Account SID
```
ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. WhatsApp Sandbox Number
```
+14155238886
```

### 3. Auth Token
```
⚠️ À récupérer dans votre console Twilio
https://www.twilio.com/console
```

---

## 🔐 Configuration Django

**Fichier:** `radgestmat/settings/development.py`

✅ **DÉJÀ CONFIGURÉ:**
```python
TWILIO_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'
```

⚠️ **À COMPLÉTER - Votre Auth Token:**

1. Allez sur: **https://www.twilio.com/console**
2. Vous verrez votre Account SID
3. À côté, cliquez sur le **cadenas** 🔒
4. Cliquez sur **"Show"** pour afficher le token
5. **Copiez** le token complet (ressemble à: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)
6. Remplacez dans `development.py`:

```python
TWILIO_AUTH_TOKEN = 'VOTRE_TOKEN_ICI'
```

---

## 🧪 Tester Immédiatement

### ÉTAPE 1: S'assurer d'avoir rejoint le WhatsApp Sandbox

✅ **Vous l'avez déjà fait!** Vous avez reçu ce code:

```
from twilio.rest import Client

account_sid = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
auth_token = '[AuthToken]'
client = Client(account_sid, auth_token)

message = client.messages.create(
  from_='whatsapp:+14155238886',
  ...
)
```

Cela signifie que vous avez **déjà rejoint** le sandbox (👍)!

### ÉTAPE 2: Ajouter votre Auth Token

Récupérez votre **Auth Token** comme décrit plus haut.

### ÉTAPE 3: Lancer le test

```bash
cd C:\Users\BlackGhost\Desktop\RadGestMat\RadGestMat
python scripts/test_twilio_quick.py
```

### ÉTAPE 4: Vérifier WhatsApp

Vous devriez recevoir un message sur **+241 62308363** dans les 10 secondes! 🔔

---

## 📞 Votre Numéro de Test

| Information | Valeur |
|------------|--------|
| **Numéro WhatsApp** | +241 62308363 (Gabon) 📱 |
| **Sandbox Twilio** | +1 415 523 8886 (USA) 🇺🇸 |
| **Status Sandbox** | ✅ ACTIF (vous avez rejoint) |
| **Type Message** | Test (Sandbox, pas de limite) |
| **Tarif** | Gratuit pendant test ✅ |

---

## 🎯 Prochaines Étapes

### Phase 1: Test Simple (MAINTENANT)
```bash
python scripts/test_twilio_quick.py
```
✅ Envoie un message test simple

### Phase 2: Test Attribution (APRÈS)
```bash
python scripts/test_whatsapp_real.py
```
✅ Crée une vraie attribution + envoie notifications

### Phase 3: Déploiement (FUTUR)
- Configurer Email (Gmail/SendGrid)
- Démarrer le scheduler APScheduler
- Mettre en production

---

## ⚡ Commandes Rapides

### Récupérer votre Auth Token
```bash
# Via Twilio CLI (si installé)
twilio api:core:accounts:fetch --sid "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Tester la Configuration Django
```bash
python manage.py shell
```
```python
from django.conf import settings
print(settings.TWILIO_ACCOUNT_SID)
print(settings.TWILIO_WHATSAPP_FROM)
```

### Vérifier que Twilio est installé
```bash
pip show twilio
```

---

## 🔗 Liens Utiles

- **Console Twilio:** https://www.twilio.com/console
- **Récupérer Auth Token:** https://www.twilio.com/console (cliquez sur cadenas)
- **WhatsApp Sandbox:** https://www.twilio.com/console/sms/whatsapp/sandbox
- **Documentation Twilio:** https://www.twilio.com/docs/whatsapp
- **Code d'exemple reçu:** `scripts/test_twilio_quick.py`

---

## ✅ Checklist

- [ ] Account SID copié: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` ✅
- [ ] Numéro Sandbox noté: `+14155238886` ✅
- [ ] Rejoins WhatsApp Sandbox ✅
- [ ] Auth Token récupéré depuis console Twilio
- [ ] Auth Token ajouté dans `settings/development.py`
- [ ] Script `test_twilio_quick.py` exécuté
- [ ] Message test reçu sur +241 62308363 🔔
- [ ] Prêt pour la Phase 2!

---

**Document Version:** 1.0  
**Créé:** December 10, 2025  
**Prêt à tester:** ✅ OUI (il manque juste votre Auth Token!)
