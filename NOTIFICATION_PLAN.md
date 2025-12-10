# 📋 PLAN DE MISE EN PLACE DES NOTIFICATIONS 
## Email et WhatsApp - RadGestMat

---

## 🎯 CONTEXTE & OBJECTIFS

### Objectif Principal
Envoyer des notifications en temps réel (Email + WhatsApp) aux :
- **Clients** : Pour les rappeler de déposer le matériel avant de partir
- **Utilisateurs** : Pour signaler la date/heure de récupération du matériel chez les clients

### Cas d'Utilisation
1. **À la création d'une Attribution (Check-out)** 
   - Notifier le client de la récupération
   - Notifier l'employé responsable
   
2. **Rappel avant la date de retour**
   - Email 24h avant la date de retour prévue
   - WhatsApp rappel (J-1, J-2)
   
3. **À la date de retour dépassée (Alerte)**
   - Notification urgente au client
   - Notification aux managers du département
   
4. **Confirmation de retour (Check-in)**
   - Confirmation au client
   - Confirmation à l'équipe

---

## 📐 ARCHITECTURE PROPOSÉE

### 1️⃣ Modèles Django

#### A) Modèle `NotificationLog` (Suivi des notifications)
```
- id (PK)
- attribution (FK -> Attribution)
- type (CREATION, RAPPEL_24H, RETARD, RESTITUTION)
- canal (EMAIL, WHATSAPP)
- destinataire (email / téléphone)
- statut (ENVOYEE, ECHEC, EN_ATTENTE)
- date_envoi
- message_id (pour WhatsApp)
- erreur_message (si echec)
- date_creation
```

#### B) Modèle `NotificationPreferences` (Préférences utilisateurs)
```
- user (FK -> User)
- client (FK -> Client)
- notifications_email (Bool) = True
- notifications_whatsapp (Bool) = False
- rappel_24h (Bool) = True
- rappel_48h (Bool) = False
- date_modification
```

#### C) Modèle `WhatsAppConfig` (Configuration WhatsApp)
```
- api_provider (TWILIO, WHATSAPP_BUSINESS)
- api_key
- phone_number_sender
- is_active
- date_creation
```

### 2️⃣ Services (Couche métier)

#### A) `NotificationService` (Service principal)
- `envoyer_notification_creation_attribution()`
- `envoyer_rappel_retour_24h()`
- `envoyer_alerte_retard()`
- `envoyer_confirmation_restitution()`
- `envoyer_notification_utilisateur()`

#### B) `EmailNotificationService` (Emails)
- `envoyer_email_client()`
- `envoyer_email_utilisateur()`
- Templating HTML/TXT

#### C) `WhatsAppNotificationService` (WhatsApp)
- `envoyer_whatsapp_client()`
- `envoyer_whatsapp_utilisateur()`
- Intégration Twilio ou WhatsApp Business API

#### D) `NotificationSchedulerService` (Tâches planifiées)
- Gestion des rappels avec Celery/APScheduler
- Vérifier les dates de retour dépassées
- Envoyer rappels J-1 et J-2

### 3️⃣ Templates Email

#### Templates à créer :
1. **Client - Check-out** : Confirmation récupération matériel
2. **Client - Rappel 24h** : Rappel de dépôt avant départ
3. **Client - Retard** : Alerte matériel non retourné
4. **Client - Check-in** : Confirmation de restitution
5. **Utilisateur - Check-out** : Notification récupération
6. **Utilisateur - Retard** : Alerte matériel non retourné
7. **Utilisateur - Check-in** : Confirmation restitution

### 4️⃣ Vues & Signaux Django

#### A) Signaux de notification
- `post_save(Attribution)` → Envoyer notification création
- `post_save(HistoriqueAttribution)` → Envoyer notification selon action

#### B) Tâches asynchrones
- Celery tasks pour envoi asynchrone
- ou APScheduler pour les rappels planifiés

#### C) Admin Dashboard
- Vue pour voir logs notifications
- Vue pour gérer préférences notifications
- Vue pour tester envois

---

## 📊 FLUX DES NOTIFICATIONS

### Scénario 1: Check-out (Récupération)
```
1. Créer Attribution → 
2. Signal déclenche notification
3. Envoyer EMAIL client + utilisateur
4. Envoyer WHATSAPP client (si activé)
5. Logger dans NotificationLog
6. Afficher confirmation UI
```

### Scénario 2: Rappel 24h avant retour
```
1. Task planifiée (chaque jour 9h du matin)
2. Vérifier Attributions avec date_retour = demain
3. Pour chaque Attribution active :
   - Vérifier préférences notification du client
   - Envoyer EMAIL rappel
   - Envoyer WHATSAPP rappel (si activé)
4. Logger chaque envoi
```

### Scénario 3: Matériel en retard
```
1. Task planifiée (chaque jour)
2. Vérifier Attributions avec date_retour < aujourd'hui ET date_retour_effective = null
3. Créer Alerte (si pas déjà créée)
4. Envoyer EMAIL urgence client + managers
5. Envoyer WHATSAPP urgence
6. Logger l'alerte
```

### Scénario 4: Check-in (Restitution)
```
1. Valider date_retour_effective →
2. Signal déclenche notification
3. Envoyer EMAIL confirmation client
4. Envoyer notification à l'équipe
5. Logger la restitution
```

---

## 🛠️ IMPLÉMENTATION ÉTAPES

### PHASE 1: Modèles & Configuration (Jour 1)
- [ ] Créer migration pour `NotificationLog`
- [ ] Créer migration pour `NotificationPreferences`
- [ ] Créer migration pour `WhatsAppConfig`
- [ ] Configurer variables d'environnement

### PHASE 2: Services Email (Jour 2)
- [ ] Implémenter `EmailNotificationService`
- [ ] Créer templates email (7 templates)
- [ ] Tests unitaires
- [ ] Ajouter au admin Django

### PHASE 3: Signaux & Tâches (Jour 3)
- [ ] Signaux Django pour Attribution
- [ ] Implémenter `NotificationService`
- [ ] Tests d'intégration

### PHASE 4: Planification (Jour 4)
- [ ] Setup APScheduler ou Celery
- [ ] Tâche pour rappels 24h/48h
- [ ] Tâche pour alertes retard
- [ ] Tests

### PHASE 5: WhatsApp (Jour 5)
- [ ] Intégration Twilio
- [ ] Implémenter `WhatsAppNotificationService`
- [ ] Tests

### PHASE 6: UI & Dashboard (Jour 6)
- [ ] Page logs notifications
- [ ] Préférences notifications (user/client)
- [ ] Tests d'envoi manuel
- [ ] Historique

### PHASE 7: Tests & Validation (Jour 7)
- [ ] Tests end-to-end
- [ ] Vérification HTML emails
- [ ] Vérification WhatsApp
- [ ] Documentation

---

## 🔧 CONFIGURATION REQUISE

### Variables d'environnement (.env)
```
# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com (ou autre)
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre_email@example.com
EMAIL_HOST_PASSWORD=votre_password
DEFAULT_FROM_EMAIL=noreply@radgestmat.com

# WhatsApp/Twilio
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+1234567890
WHATSAPP_ENABLED=True

# Scheduler
SCHEDULER_ENABLED=True
SCHEDULER_HOUR=9  # heure d'exécution des tâches
```

### Dépendances à ajouter
```
- twilio>=7.0.0
- APScheduler>=3.10.0 (ou celery)
- celery>=5.3.0 (optionnel, alternative)
```

---

## 📧 CONTENU EMAIL EXEMPLE

### Subject
```
[RadGestMat] Confirmation: Matériel récupéré
[RadGestMat] ⏰ Rappel: Veuillez restituer le matériel
[RadGestMat] ⚠️ URGENT: Matériel non retourné
```

### Structure HTML
```
- Header avec logo RadGestMat
- Titre et message principal
- Détails matériel/attribution
- Date/heure clé
- Bouton action (lien dashboard)
- Footer avec infos contact
```

---

## 📱 CONTENU WHATSAPP EXEMPLE

### Message court
```
"🔔 RadGestMat - Bonjour, vous avez récupéré 
un matériel. À retourner avant le 2025-01-15. 
Détails: https://app.radgestmat.com/attribution/123"

"⏰ Rappel: Veuillez retourner le matériel 
demain avant votre départ. Merci!"

"⚠️ URGENT: Matériel non retourné depuis 
2025-01-12. Veuillez contacter l'équipe."
```

---

## ✅ CRITÈRES DE SUCCÈS

- [x] Notifications envoyées automatiquement
- [x] Logs complets pour audit
- [x] Préférences utilisateurs respectées
- [x] Pas d'envois en double
- [x] Gestion des erreurs d'envoi
- [x] Dashboard de suivi
- [x] Tests unitaires & intégration
- [x] Documentation

---

## 🚨 CONSIDÉRATIONS IMPORTANTES

1. **Consentement RGPD** : Obtenir accord clients pour SMS/WhatsApp
2. **Coûts** : WhatsApp/SMS = frais (prévoir budget)
3. **Rate limiting** : Vérifier limites API Twilio
4. **Fallback** : Si WhatsApp échoue, envoyer email
5. **Timezone** : Gérer les décalages horaires
6. **Templates multilingues** : FR/EN si nécessaire

---

## 📚 RESSOURCES

- Twilio Docs: https://www.twilio.com/docs/whatsapp
- Django Signals: https://docs.djangoproject.com/en/stable/topics/signals/
- APScheduler: https://apscheduler.readthedocs.io/
- Email Templates Best Practices: https://www.litmus.com/

