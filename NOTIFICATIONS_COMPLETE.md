# 📚 Documentation Complète - Système de Notifications RadGestMat

## 🎯 Vue d'Ensemble

Ce document regroupe l'implémentation complète du système de notifications multi-canal (Email + WhatsApp) pour RadGestMat, comprenant **6 phases** de développement.

---

## 📋 Table des Matières

1. [Phase 1: Modèles de Données](#phase-1-modèles-de-données)
2. [Phase 2: Service Email](#phase-2-service-email)
3. [Phase 3: Signaux Django](#phase-3-signaux-django)
4. [Phase 4: APScheduler](#phase-4-apscheduler)
5. [Phase 5: WhatsApp/Twilio](#phase-5-whatsapptwilio)
6. [Phase 6: Dashboard Admin](#phase-6-dashboard-admin)
7. [Configuration](#configuration)
8. [Tests](#tests)
9. [Déploiement](#déploiement)

---

## Phase 1: Modèles de Données

### 📊 Modèles Créés

#### 1. `NotificationLog`
**Objectif**: Tracer toutes les notifications envoyées

```python
# assets/models.py
class NotificationLog(models.Model):
    TYPE_CHOICES = [
        ('CREATION', 'Notification de création'),
        ('RAPPEL_2H', 'Rappel 2h avant'),
        ('RAPPEL_J_MOINS_2', 'Rappel J-2'),
        ('RAPPEL_J_MOINS_1', 'Rappel J-1'),
        ('RAPPEL_FINAL', 'Rappel jour retour'),
        ('RETARD', 'Alerte retard'),
        ('RESTITUTION', 'Confirmation restitution'),
    ]
    
    CANAL_CHOICES = [
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp'),
    ]
    
    attribution = ForeignKey(Attribution)
    type_notification = CharField(max_length=20, choices=TYPE_CHOICES)
    canal = CharField(max_length=20, choices=CANAL_CHOICES)
    statut = CharField(max_length=20, choices=STATUT_CHOICES)
    date_envoi = DateTimeField(auto_now_add=True)
    nb_tentatives = IntegerField(default=1)
```

**Utilité**:
- Audit complet des notifications
- Traçabilité des envois
- Statistiques de performance

#### 2. `NotificationPreferences`
**Objectif**: Gérer les préférences utilisateur

```python
class NotificationPreferences(models.Model):
    user = OneToOneField(User, null=True, blank=True)
    client = OneToOneField(Client, null=True, blank=True)
    
    # Canaux
    notifications_email = BooleanField(default=True)
    notifications_whatsapp = BooleanField(default=False)
    phone_number = CharField(max_length=20, null=True, blank=True)
    
    # Rappels
    rappel_j_moins_2 = BooleanField(default=True)
    rappel_j_moins_1 = BooleanField(default=True)
    rappel_final = BooleanField(default=True)
    rappel_2h_avant = BooleanField(default=True)
```

**Utilité**:
- Personnalisation par utilisateur
- Opt-in/Opt-out par canal
- Configuration des rappels souhaités

#### 3. `WhatsAppConfig`
**Objectif**: Configuration API WhatsApp

```python
class WhatsAppConfig(models.Model):
    api_provider = CharField(max_length=20, default='TWILIO')
    api_key = CharField(max_length=255)
    api_secret = CharField(max_length=255, null=True, blank=True)
    phone_number_sender = CharField(max_length=20)
    is_active = BooleanField(default=False)
```

**Utilité**:
- Stockage sécurisé des credentials Twilio
- Multi-provider support (extensible)

#### 4. Extension `Attribution`
**Nouveaux champs**:
```python
duree_emprunt = CharField(
    max_length=10,
    choices=[
        ('COURT', 'Court terme (< 4h)'),
        ('MOYEN', 'Moyen terme (4h - 24h)'),
        ('LONG', 'Long terme (> 24h)'),
    ],
    default='LONG'
)
heure_retour_prevue = TimeField(null=True, blank=True)
heure_retour_effective = TimeField(null=True, blank=True)
```

### 📝 Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Phase 2: Service Email

### 📧 `NotificationEmailService`

**Fichier**: `assets/services.py`

#### Méthodes Principales

1. **Notification de Création**
```python
@staticmethod
def envoyer_notification_creation(attribution: Attribution) -> dict:
    """Envoie un email de confirmation de création d'attribution"""
```

2. **Rappels Programmés**
```python
@staticmethod
def envoyer_rappel_j_minus_2(attribution: Attribution) -> dict:
    """Rappel J-2 pour emprunts long terme"""

@staticmethod
def envoyer_rappel_j_minus_1(attribution: Attribution) -> dict:
    """Rappel J-1 pour emprunts long terme"""

@staticmethod
def envoyer_rappel_final(attribution: Attribution) -> dict:
    """Rappel jour du retour pour emprunts long terme"""

@staticmethod
def envoyer_rappel_2h_avant(attribution: Attribution) -> dict:
    """Rappel 2h avant pour emprunts moyen terme"""
```

3. **Alertes**
```python
@staticmethod
def envoyer_alerte_retard(attribution: Attribution) -> dict:
    """Alerte de retard"""

@staticmethod
def envoyer_notification_restitution(attribution: Attribution) -> dict:
    """Confirmation de restitution"""
```

### 📄 Templates Email

7 templates HTML créés dans `templates/assets/emails/`:

1. `notification_base.html` - Template de base
2. `notification_creation.html` - Confirmation création
3. `notification_rappel_j2.html` - Rappel J-2
4. `notification_rappel_j1.html` - Rappel J-1
5. `notification_rappel_final.html` - Rappel final
6. `notification_rappel_2h.html` - Rappel 2h
7. `notification_retard.html` - Alerte retard
8. `notification_restitution.html` - Confirmation retour

**Design**:
- Responsive
- Branding RadGestMat
- Icons Font Awesome
- Informations claires et complètes

### 🧪 Test
```bash
python scripts/test_notifications.py
```

---

## Phase 3: Signaux Django

### 🔔 Fichier `assets/signals.py`

#### Signal 1: Notification de Création

```python
@receiver(post_save, sender=Attribution)
def envoyer_notifications_attribution(sender, instance, created, **kwargs):
    if created:
        # Récupérer les préférences
        preferences, _ = NotificationPreferences.objects.get_or_create(
            user=instance.client
        )
        
        # Email (si activé)
        if preferences.notifications_email:
            NotificationEmailService.envoyer_notification_creation(instance)
        
        # WhatsApp (si activé)
        if preferences.notifications_whatsapp:
            WhatsAppService.envoyer_notification_creation(instance)
```

#### Signal 2: Notification de Restitution

```python
@receiver(pre_save, sender=Attribution)
def detecter_retour_materiel(sender, instance, **kwargs):
    """Détecte si date_retour_effective vient d'être définie"""
    if instance.pk:
        old_instance = Attribution.objects.get(pk=instance.pk)
        if not old_instance.date_retour_effective and instance.date_retour_effective:
            instance._notification_restitution_required = True

@receiver(post_save, sender=Attribution)
def envoyer_notifications_attribution(sender, instance, created, **kwargs):
    elif hasattr(instance, '_notification_restitution_required'):
        # Envoyer confirmations de restitution
        NotificationEmailService.envoyer_notification_restitution(instance)
        WhatsAppService.envoyer_notification_restitution(instance)
```

### ✅ Activation

Les signaux sont automatiquement activés via `assets/apps.py`:

```python
class AssetsConfig(AppConfig):
    def ready(self):
        import assets.signals  # Charge les signaux
```

### 🧪 Test
```bash
python scripts/test_notifications_complete.py
```

**Résultat attendu**:
- Création d'attribution → Email + WhatsApp envoyés
- Retour de matériel → Confirmations envoyées
- Logs dans `NotificationLog`

---

## Phase 4: APScheduler

### ⏰ Architecture

**Fichiers créés**:
1. `assets/scheduler.py` - Configuration APScheduler
2. `assets/scheduler_jobs.py` - Définition des jobs
3. `assets/management/commands/run_scheduler.py` - Commande Django

### 📅 Jobs Configurés

#### 1. Rappels J-2 (Long Terme)
**Fréquence**: Toutes les heures  
**Heure**: 09:00  
```python
@job(id='rappels_j_minus_2', replace_existing=True)
def envoyer_rappels_j_minus_2():
    """Rappels 2 jours avant le retour"""
```

#### 2. Rappels J-1 (Long Terme)
**Fréquence**: Toutes les heures  
**Heure**: 09:00  
```python
@job(id='rappels_j_minus_1', replace_existing=True)
def envoyer_rappels_j_minus_1():
    """Rappels 1 jour avant le retour"""
```

#### 3. Rappels Finaux (Long Terme)
**Fréquence**: Toutes les heures  
**Heure**: 08:00  
```python
@job(id='rappels_finaux', replace_existing=True)
def envoyer_rappels_finaux():
    """Rappels le jour du retour"""
```

#### 4. Rappels 2h Avant (Moyen Terme)
**Fréquence**: Toutes les 30 minutes  
```python
@job(id='rappels_2h_avant', replace_existing=True)
def envoyer_rappels_2h_avant():
    """Rappels 2h avant pour emprunts 4h-24h"""
```

#### 5. Alertes de Retard
**Fréquence**: Toutes les heures  
**Heure**: 10:00  
```python
@job(id='alertes_retard', replace_existing=True)
def detecter_et_notifier_retards():
    """Alertes pour matériels en retard"""
```

### 🚀 Lancement

**En développement**:
```bash
python manage.py run_scheduler
```

**En production (systemd)**:
```ini
[Unit]
Description=RadGestMat Scheduler
After=network.target

[Service]
Type=simple
User=radgestmat
WorkingDirectory=/path/to/RadGestMat
ExecStart=/path/to/env/bin/python manage.py run_scheduler
Restart=always

[Install]
WantedBy=multi-user.target
```

### 📊 Logs
```bash
tail -f logs/scheduler.log
```

---

## Phase 5: WhatsApp/Twilio

### 💬 Configuration Twilio

#### 1. Credentials (Development)

**Fichier**: `radgestmat/settings/development.py`

```python
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_AUTH_TOKEN = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'
```

#### 2. Twilio Sandbox

**Activation**:
1. Envoyer sur WhatsApp à `+1 415 523 8886`
2. Message: `join <code>` (code fourni par Twilio Console)
3. Attendre confirmation

**Téléphone de test**: `+24105339274` (Gabon)

### 📱 `WhatsAppService`

**Fichier**: `assets/whatsapp_service.py`

#### Méthodes

```python
class WhatsAppService:
    @staticmethod
    def envoyer_notification_creation(attribution: Attribution) -> dict:
        """WhatsApp de création"""
    
    @staticmethod
    def envoyer_rappel_j_minus_2(attribution: Attribution) -> dict:
        """WhatsApp rappel J-2"""
    
    @staticmethod
    def envoyer_rappel_j_minus_1(attribution: Attribution) -> dict:
        """WhatsApp rappel J-1"""
    
    @staticmethod
    def envoyer_rappel_final(attribution: Attribution) -> dict:
        """WhatsApp rappel final"""
    
    @staticmethod
    def envoyer_rappel_2h_avant(attribution: Attribution) -> dict:
        """WhatsApp rappel 2h"""
    
    @staticmethod
    def envoyer_alerte_retard(attribution: Attribution) -> dict:
        """WhatsApp alerte retard"""
    
    @staticmethod
    def envoyer_notification_restitution(attribution: Attribution) -> dict:
        """WhatsApp confirmation retour"""
```

### 📝 Templates SMS

**Fichier**: `assets/whatsapp_templates.py`

7 templates avec emojis et formatage:

```python
TEMPLATE_CREATION = """
🎯 NOUVELLE ATTRIBUTION - RadGestMat

📦 Matériel: {materiel_nom}
🆔 Asset ID: {asset_id}
📅 Retour prévu: {date_retour}
⏰ Heure: {heure_retour}

📋 Motif: {motif}

✅ Attribution confirmée!
"""
```

### 🧪 Tests

1. **Test direct**:
```bash
python scripts/test_whatsapp_final.py
```

2. **Test avec attribution**:
```bash
python scripts/test_notifications_complete.py
```

**Résultat attendu**:
- ✅ Message SID retourné
- ✅ Status: queued → sent → delivered
- ✅ Réception WhatsApp sur téléphone

### ⚠️ Limitations Sandbox

- **Sandbox**: Messages uniquement vers numéros validés
- **Templates**: Texte libre (pas de templates approuvés nécessaires)
- **Volume**: Limité pour tests

**Migration Production**:
1. Créer compte WhatsApp Business
2. Soumettre templates pour approbation
3. Configurer numéro WhatsApp Business
4. Mettre à jour credentials dans settings

---

## Phase 6: Dashboard Admin

### 📊 Dashboard Notifications

**URL**: `/notifications/dashboard/`

**Fonctionnalités**:
1. **Statistiques Globales**
   - Total notifications envoyées
   - Taux de succès
   - Répartition Email/WhatsApp

2. **Statistiques par Type**
   - Création
   - Rappels (J-2, J-1, Final, 2h)
   - Retard
   - Restitution

3. **Historique**
   - 50 dernières notifications
   - Filtres par statut
   - Détails par notification

**Template**: `templates/assets/notifications_dashboard.html`

**Vue**: `assets/views.py::notifications_dashboard()`

**Permissions**: `SUPER_ADMIN` et `DEPT_MANAGER` uniquement

### ⚙️ Préférences Utilisateur

**URL**: `/notifications/preferences/`

**Fonctionnalités**:
1. **Choix des Canaux**
   - Email On/Off
   - WhatsApp On/Off
   - Numéro WhatsApp

2. **Choix des Rappels**
   - Long terme: J-2, J-1, Final
   - Moyen terme: 2h avant

**Template**: `templates/assets/notification_preferences.html`

**Vue**: `assets/views.py::notification_preferences()`

**Permissions**: Tous utilisateurs connectés

### 🎨 Design

- Interface moderne et responsive
- Cards Bootstrap
- Icons Font Awesome
- Badges colorés par statut
- Charts simples (HTML/CSS)

---

## Configuration

### 📧 Email Backend

**Development**:
```python
# settings/development.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Production (Gmail)**:
```python
# settings/production.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@gmail.com'
EMAIL_HOST_PASSWORD = 'votre-app-password'
DEFAULT_FROM_EMAIL = 'RadGestMat <noreply@radgestmat.com>'
```

**Production (SendGrid)**:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'votre-sendgrid-api-key'
```

### 💬 WhatsApp Backend

**Development (Sandbox)**:
```python
TWILIO_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_AUTH_TOKEN = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'
```

**Production**:
```python
TWILIO_ACCOUNT_SID = 'votre-production-sid'
TWILIO_AUTH_TOKEN = 'votre-production-token'
TWILIO_WHATSAPP_FROM = 'whatsapp:+votre-numero-business'
```

---

## Tests

### 🧪 Tests Disponibles

1. **Test Email**:
```bash
python scripts/test_notifications.py
```

2. **Test WhatsApp**:
```bash
python scripts/test_whatsapp_final.py
```

3. **Test Complet (Signaux)**:
```bash
python scripts/test_notifications_complete.py
```

4. **Test Scheduler** (jobs individuels):
```bash
python scripts/test_scheduler_jobs.py
```

### ✅ Checklist de Validation

- [ ] Migration 0007 appliquée
- [ ] Email console backend fonctionne
- [ ] WhatsApp Sandbox configuré
- [ ] Signaux activés (apps.py)
- [ ] Création attribution → notifications envoyées
- [ ] Retour matériel → confirmations envoyées
- [ ] Dashboard accessible
- [ ] Préférences modifiables
- [ ] Scheduler démarre sans erreur
- [ ] Jobs s'exécutent correctement

---

## Déploiement

### 📦 Prérequis Production

1. **Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Variables d'environnement**:
```bash
export DJANGO_SETTINGS_MODULE=radgestmat.settings.production
export TWILIO_ACCOUNT_SID=your-sid
export TWILIO_AUTH_TOKEN=your-token
export EMAIL_HOST_PASSWORD=your-password
```

3. **Migrations**:
```bash
python manage.py migrate
```

4. **Static files**:
```bash
python manage.py collectstatic --noinput
```

### 🚀 Services

#### 1. Gunicorn (Web)
```bash
gunicorn radgestmat.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120
```

#### 2. APScheduler (Background)
```bash
python manage.py run_scheduler
```

#### 3. Nginx (Reverse Proxy)
```nginx
server {
    listen 80;
    server_name radgestmat.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        alias /var/www/radgestmat/staticfiles/;
    }
}
```

### 📊 Monitoring

**Logs**:
```bash
# Django
tail -f logs/radgestmat.log

# Scheduler
tail -f logs/scheduler.log

# Notifications
tail -f logs/notifications.log
```

**Métriques**:
- Taux de succès des notifications (dashboard)
- Temps de traitement des jobs (scheduler logs)
- Erreurs Twilio (console Twilio)

---

## 📚 Ressources

### Documentation

- [Django Signals](https://docs.djangoproject.com/en/5.0/topics/signals/)
- [APScheduler](https://apscheduler.readthedocs.io/)
- [Twilio WhatsApp](https://www.twilio.com/docs/whatsapp)
- [Django Email](https://docs.djangoproject.com/en/5.0/topics/email/)

### Support

- GitHub Issues: `https://github.com/BlackGhost99/RadGestMat/issues`
- Email: support@radgestmat.com

---

**Version**: 1.0.0  
**Date**: 10 Décembre 2025  
**Auteur**: RadGestMat Team  
**Status**: ✅ Complet & Testé
