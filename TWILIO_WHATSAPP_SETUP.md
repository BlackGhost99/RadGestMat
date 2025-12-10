# 📱 Configuration WhatsApp avec Twilio - Guide Complet

**Pour:** RadGestMat Notification System  
**Numéro cible:** +241 62308363 (Gabon)

---

## 🎯 Objectif

Configurer Twilio pour pouvoir envoyer des notifications WhatsApp au numéro gabonais **+241 62308363**.

---

## 📋 Option 1: WhatsApp Sandbox (RECOMMANDÉ pour Test)

### ✅ Avantages
- ✅ **Gratuit** pour tester
- ✅ **Immédiat** (5 minutes)
- ✅ Pas besoin d'approbation
- ✅ Parfait pour développement

### 📝 Étapes de Configuration

#### 1. Créer un compte Twilio

🔗 **Lien:** https://www.twilio.com/try-twilio

1. Cliquez sur "Sign up"
2. Remplissez le formulaire:
   - Email
   - Mot de passe
   - Nom
3. Vérifiez votre email
4. Vérifiez votre numéro de téléphone (+241 62308363)

#### 2. Activer WhatsApp Sandbox

🔗 **Lien:** https://www.twilio.com/console/sms/whatsapp/sandbox

1. Connectez-vous à votre compte Twilio
2. Allez dans: **Messaging** → **Try it out** → **Send a WhatsApp message**
3. Vous verrez un message comme:

```
To connect your sandbox, send:
join <code-unique>

To: +1 415 523 8886 (US number)
```

4. **Sur votre téléphone (+241 62308363):**
   - Ouvrez WhatsApp
   - Créez un nouveau message
   - Destinataire: **+1 415 523 8886** (ou le numéro affiché)
   - Message: **join <votre-code>** (ex: `join shadow-mountain`)
   - Envoyez le message

5. Vous recevrez une confirmation:
```
✅ Your Sandbox is now active
You can now receive messages from this number
```

#### 3. Récupérer vos Credentials

🔗 **Lien:** https://www.twilio.com/console

Dans le Dashboard Twilio, vous verrez:

```
Account SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Auth Token: [cliquez sur "Show" pour voir]
```

**Copiez ces deux valeurs!**

#### 4. Configurer Django

Ouvrez: `radgestmat/settings/development.py`

Ajoutez à la fin du fichier:

```python
# ========================================
# Twilio WhatsApp Configuration
# ========================================
TWILIO_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'  # Votre Account SID
TWILIO_AUTH_TOKEN = 'your_auth_token_here'  # Votre Auth Token
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'  # Numéro sandbox (peut varier)
```

**⚠️ Remplacez:**
- `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` par votre vrai Account SID
- `your_auth_token_here` par votre vrai Auth Token
- Le numéro `+14155238886` par le numéro sandbox affiché dans votre console

#### 5. Tester l'envoi

Exécutez le script de test:

```bash
cd C:\Users\BlackGhost\Desktop\RadGestMat\RadGestMat
python scripts/test_whatsapp_real.py
```

**Résultat attendu:**
```
🎉 SUCCÈS! Message WhatsApp envoyé!
✅ Status: ENVOYEE
✅ Date d'envoi: 2025-12-10 15:30:00
📱 Vérifiez votre WhatsApp (+24162308363)
```

**Vous recevrez sur WhatsApp:**
```
✅ Emprunt Confirmé

Bonjour Client Test Gabon!

Votre demande d'emprunt a été confirmée:

📦 Matériel: Ordinateur Portable Test
🏷️ Référence: LAPTOP-TEST-001
📅 Date retour: 2025-12-10
🕐 Heure retour: 18:30

✅ Vous pouvez retirer le matériel au point de distribution.

Pour toute question, contactez-nous!
```

---

## 📋 Option 2: WhatsApp Business API (Production)

### ⚠️ Avertissement

- ⚠️ Nécessite **validation par Meta/Facebook**
- ⚠️ Peut prendre **plusieurs jours**
- ⚠️ Nécessite un **compte Business vérifié**
- 💰 **Payant** après période d'essai

### 📝 Étapes (Résumé)

1. Créer un compte WhatsApp Business
2. Demander l'accès à l'API WhatsApp via Twilio
3. Soumettre les documents d'entreprise
4. Attendre l'approbation (3-7 jours)
5. Obtenir un numéro WhatsApp dédié
6. Configurer les templates de messages

**👉 Recommandation:** Utilisez d'abord le Sandbox pour développer et tester.

---

## 🔧 Configuration Sécurisée (Production)

Pour la production, utilisez des **variables d'environnement** au lieu de mettre les credentials directement dans le code.

### Méthode 1: Fichier `.env`

1. Créez un fichier `.env` à la racine du projet:

```env
# .env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

2. Installez `python-decouple`:

```bash
pip install python-decouple
```

3. Dans `settings/development.py`:

```python
from decouple import config

TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_FROM = config('TWILIO_WHATSAPP_FROM')
```

4. Ajoutez `.env` au `.gitignore`:

```
# .gitignore
.env
```

### Méthode 2: Variables d'environnement Windows

```bash
# Dans PowerShell
$env:TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:TWILIO_AUTH_TOKEN="your_auth_token_here"
$env:TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"
```

Dans `settings/development.py`:

```python
import os

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM')
```

---

## 🧪 Tester la Configuration

### Test 1: Vérifier les credentials

```bash
python manage.py shell
```

```python
from django.conf import settings

print("Account SID:", settings.TWILIO_ACCOUNT_SID[:10] + "...")
print("Auth Token:", "***" if settings.TWILIO_AUTH_TOKEN else "NON CONFIGURÉ")
print("WhatsApp From:", settings.TWILIO_WHATSAPP_FROM)
```

### Test 2: Envoyer un message de test

```bash
python scripts/test_whatsapp_real.py
```

### Test 3: Créer une vraie attribution

```bash
python manage.py shell
```

```python
from django.utils import timezone
from datetime import timedelta
from users.models import User, Departement
from assets.models import Materiel, Client, Attribution, CategorieMateriels

# Créer les objets nécessaires
dept = Departement.objects.get(code='INFO')
user = User.objects.get(username='admin_test')
client = Client.objects.get(phone='+24162308363')
mat = Materiel.objects.get(code='LAPTOP-TEST-001')

# Créer attribution
now = timezone.now()
attr = Attribution.objects.create(
    materiel=mat,
    client=client,
    date_emprunt=now.date(),
    heure_emprunt=now.time(),
    date_retour_prevue=(now + timedelta(days=2)).date(),
    heure_retour_prevue=(now + timedelta(days=2)).time(),
    departement=dept,
    utilisateur_attribution=user,
    raison='Test manuel WhatsApp'
)

# Envoyer notification
from assets.whatsapp_service import WhatsAppNotificationService
result = WhatsAppNotificationService.send_creation_notification(
    attr, 
    '+24162308363'
)

print("✅ Envoyé!" if result else "❌ Échec")
```

---

## ❌ Résolution de Problèmes

### Problème 1: "Authentication Error"

**Cause:** Account SID ou Auth Token incorrect

**Solution:**
1. Vérifiez sur https://www.twilio.com/console
2. Copiez à nouveau les credentials
3. Assurez-vous qu'il n'y a pas d'espaces avant/après

### Problème 2: "Invalid 'To' Phone Number"

**Cause:** Le numéro n'est pas connecté au sandbox

**Solution:**
1. Allez sur https://www.twilio.com/console/sms/whatsapp/sandbox
2. Vérifiez que +24162308363 est dans la liste "Active Participants"
3. Si non, renvoyez `join <code>` depuis ce numéro

### Problème 3: "Permission Denied"

**Cause:** Le numéro sandbox n'est pas vérifié

**Solution:**
- Attendez 24h après avoir envoyé `join <code>`
- Vérifiez le statut dans la console Twilio
- Assurez-vous d'utiliser le bon numéro sandbox

### Problème 4: Message reçu mais pas formaté

**Cause:** Template incorrect

**Solution:**
- Vérifiez `assets/whatsapp_templates.py`
- Les emojis sont bien supportés
- Le format est bien respecté

---

## 📊 Limitations du Sandbox

| Limite | Valeur |
|--------|--------|
| Messages par jour | 100 |
| Participants actifs | 5 |
| Durée de session | 24h (doit rejoindre chaque jour) |
| Tarif | **Gratuit** |

**Pour production:** Passez à WhatsApp Business API (pas de limite, mais payant).

---

## 💰 Tarifs Production

### WhatsApp Business API (via Twilio)

- **Conversation initiée par entreprise:** ~$0.04 - $0.10 par message
- **Conversation initiée par client:** Gratuit (24h)
- **Templates approuvés:** Requis pour initier conversations
- **Pas de limite** de messages

### Calcul pour RadGestMat

Si vous envoyez **100 notifications/jour**:
- 100 messages × $0.05 = **$5/jour**
- **$150/mois** pour 3,000 messages
- Ou **$1,800/an**

**💡 Optimisation:** Utilisez email comme canal principal, WhatsApp en option.

---

## ✅ Checklist de Configuration

Avant de tester:

- [ ] Compte Twilio créé
- [ ] Email vérifié
- [ ] Téléphone vérifié (+241 62308363)
- [ ] WhatsApp Sandbox activé
- [ ] Message `join <code>` envoyé
- [ ] Confirmation reçue sur WhatsApp
- [ ] Account SID copié
- [ ] Auth Token copié
- [ ] Numéro sandbox copié
- [ ] Credentials ajoutés dans `settings/development.py`
- [ ] Script `test_whatsapp_real.py` créé
- [ ] Test exécuté avec succès
- [ ] Message WhatsApp reçu sur téléphone

---

## 🎯 Prochaines Étapes

Après avoir configuré et testé:

1. **Phase 3:** Implémenter les signaux Django pour auto-send
2. **Phase 6:** Créer l'interface utilisateur de préférences
3. **Production:** Migrer vers WhatsApp Business API
4. **Optimisation:** Ajouter fallback email si WhatsApp échoue

---

## 📞 Support

**Twilio Support:**
- Console: https://www.twilio.com/console
- Documentation: https://www.twilio.com/docs/whatsapp
- Support: https://support.twilio.com

**RadGestMat Docs:**
- PHASE5_IMPLEMENTATION.md
- QUICKSTART_GUIDE.md
- test_whatsapp_real.py

---

**Document Version:** 1.0  
**Date:** December 10, 2025  
**Testé avec:** Twilio WhatsApp Sandbox, Numéro Gabon (+241 62308363)
