# 📅 GESTION DES NOTIFICATIONS PAR DURÉE D'EMPRUNT

## Classification des emprunts

```
┌─────────────────────────────────────────────────────────────┐
│ DURÉE = date_retour_prevue - date_attribution              │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────┐
│  COURT TERME: 0 à 4 heures           │
├──────────────────────────────────────┤
│ Exemple: 14h00 → 18h00               │
│ Rappels: AUCUN (trop court)          │
│ Alerte retard: Si > heure retour +30 │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  MOYEN TERME: 4 à 24 heures          │
├──────────────────────────────────────┤
│ Exemple: 09h00 → 18h00 (même jour)  │
│ Exemple: 14h00 → 14h00 (jour suivant)│
│ Rappels: 1 rappel à 2h avant retour  │
│ Alerte retard: Si > heure retour +30 │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  LONG TERME: > 24 heures             │
├──────────────────────────────────────┤
│ Exemple: 09h00 lundi → 09h00 vendredi│
│ Rappels: J-2, J-1 (10h du matin)    │
│ Alerte retard: Si > 10h du jour retour│
└──────────────────────────────────────┘
```

---

## Modèle Attribution modifié

```python
# Ajouter à Attribution:
DUREE_COURT_TERME = 'COURT'    # 0-4h
DUREE_MOYEN_TERME = 'MOYEN'    # 4h-24h
DUREE_LONG_TERME = 'LONG'      # >24h

DUREE_CHOICES = [
    (DUREE_COURT_TERME, 'Court terme (< 4h)'),
    (DUREE_MOYEN_TERME, 'Moyen terme (4h - 24h)'),
    (DUREE_LONG_TERME, 'Long terme (> 24h)'),
]

class Attribution(models.Model):
    # ... champs existants ...
    
    # NOUVEAU: Champs pour durée d'emprunt
    duree_emprunt = models.CharField(
        max_length=10,
        choices=DUREE_CHOICES,
        default=DUREE_LONG_TERME,
        help_text="Catégorie automatique basée sur la durée"
    )
    
    # NOUVEAU: Heures de retour (pour court/moyen terme)
    heure_retour_prevue = models.TimeField(
        null=True,
        blank=True,
        help_text="Heure de retour prévue (pour emprunts < 24h)"
    )
    heure_retour_effective = models.TimeField(
        null=True,
        blank=True,
        help_text="Heure effective de retour"
    )
    
    def calculate_duree_emprunt(self):
        """Calcul automatique de la catégorie de durée"""
        if not self.date_retour_prevue:
            return self.DUREE_LONG_TERME
            
        # Conversion en datetime pour calcul précis
        from django.utils import timezone
        from datetime import datetime, time
        
        if isinstance(self.date_attribution, datetime):
            start = self.date_attribution
        else:
            start = datetime.combine(self.date_attribution, time.min)
        
        if self.heure_retour_prevue:
            end = datetime.combine(
                self.date_retour_prevue,
                self.heure_retour_prevue
            )
        else:
            end = datetime.combine(self.date_retour_prevue, time.min)
        
        delta = end - start
        hours = delta.total_seconds() / 3600
        
        if hours <= 4:
            return self.DUREE_COURT_TERME
        elif hours <= 24:
            return self.DUREE_MOYEN_TERME
        else:
            return self.DUREE_LONG_TERME
    
    def save(self, *args, **kwargs):
        # ... code existant ...
        
        # AUTO-CALCULER la durée
        self.duree_emprunt = self.calculate_duree_emprunt()
        
        super().save(*args, **kwargs)
```

---

## Logique de notifications par durée

### 🟢 **COURT TERME (0-4h)**

**À la création:**
- ✉️ EMAIL CLIENT: Confirmation rapide
- Pas de rappel (trop court)

**Monitoring:**
```python
# Vérifier chaque 15 min si heure_retour_effective == heure_retour_prevue
# Seuil: +30 minutes → ALERTE RETARD

if datetime.now() > heure_retour_prevue + 30min AND date_retour_effective == NULL:
    → ALERTE CLIENT + MANAGER
```

**À la restitution:**
- ✉️ EMAIL: Confirmation restitution

---

### 🟡 **MOYEN TERME (4h-24h)**

**À la création:**
- ✉️ EMAIL CLIENT: Détails complets
- 💬 WHATSAPP: Confirmation brève

**Rappel unique:**
```python
# 2 heures avant heure_retour_prevue

timestamp_rappel = datetime.combine(
    date_retour_prevue,
    heure_retour_prevue
) - timedelta(hours=2)

scheduler.add_job(
    send_reminder_notification,
    trigger='date',
    run_date=timestamp_rappel,
    args=[attribution_id]
)
```

**Monitoring:**
```python
# Vérifier chaque 30 min
if datetime.now() > heure_retour_prevue + 30min AND date_retour_effective == NULL:
    → ALERTE RETARD (CLIENT + MANAGER)
```

---

### 🔵 **LONG TERME (>24h)**

**À la création:**
- ✉️ EMAIL CLIENT: Détails + conditions
- 💬 WHATSAPP: Info retour prévu

**Rappels multiples:**
```python
# J-2 à 10h
scheduler.add_job(
    send_reminder_notification,
    trigger='date',
    run_date=datetime.combine(date_retour_prevue - 2 days, time(10, 0)),
    args=[attribution_id, 'RAPPEL_J_MOINS_2']
)

# J-1 à 10h
scheduler.add_job(
    send_reminder_notification,
    trigger='date',
    run_date=datetime.combine(date_retour_prevue - 1 day, time(10, 0)),
    args=[attribution_id, 'RAPPEL_J_MOINS_1']
)

# Jour retour à 08h (rappel final)
scheduler.add_job(
    send_reminder_notification,
    trigger='date',
    run_date=datetime.combine(date_retour_prevue, time(8, 0)),
    args=[attribution_id, 'RAPPEL_FINAL']
)
```

**Monitoring (quotidien à 14h):**
```python
# Chercher les attributions en retard
overdue_attributions = Attribution.objects.filter(
    date_retour_prevue__lt=today(),
    date_retour_effective__isnull=True
)

for attr in overdue_attributions:
    days_late = (today() - attr.date_retour_prevue).days
    
    if days_late == 0:
        severite = CRITICAL  # Jour même du retour
    elif days_late <= 3:
        severite = WARNING   # Moins de 3 jours
    else:
        severite = CRITICAL  # Plus de 3 jours
    
    create_alert(attr, severite, days_late)
```

---

## Modèle NotificationLog amélioré

```python
class NotificationLog(models.Model):
    TYPE_CREATION = 'CREATION'
    TYPE_RAPPEL_2H = 'RAPPEL_2H'
    TYPE_RAPPEL_J_MOINS_2 = 'RAPPEL_J_MOINS_2'
    TYPE_RAPPEL_J_MOINS_1 = 'RAPPEL_J_MOINS_1'
    TYPE_RAPPEL_FINAL = 'RAPPEL_FINAL'
    TYPE_RETARD = 'RETARD'
    TYPE_RESTITUTION = 'RESTITUTION'
    
    TYPE_CHOICES = [
        (TYPE_CREATION, 'Notification de création'),
        (TYPE_RAPPEL_2H, 'Rappel 2h avant'),
        (TYPE_RAPPEL_J_MOINS_2, 'Rappel J-2'),
        (TYPE_RAPPEL_J_MOINS_1, 'Rappel J-1'),
        (TYPE_RAPPEL_FINAL, 'Rappel jour retour'),
        (TYPE_RETARD, 'Alerte retard'),
        (TYPE_RESTITUTION, 'Confirmation restitution'),
    ]
    
    CANAL_EMAIL = 'EMAIL'
    CANAL_WHATSAPP = 'WHATSAPP'
    CANAL_CHOICES = [
        (CANAL_EMAIL, 'Email'),
        (CANAL_WHATSAPP, 'WhatsApp'),
    ]
    
    STATUT_ENVOYEE = 'ENVOYEE'
    STATUT_ECHEC = 'ECHEC'
    STATUT_ECHEC_PERMANENT = 'ECHEC_PERM'
    STATUT_CHOICES = [
        (STATUT_ENVOYEE, 'Envoyée'),
        (STATUT_ECHEC, 'Échec (retry en cours)'),
        (STATUT_ECHEC_PERMANENT, 'Échec définitif'),
    ]
    
    attribution = models.ForeignKey(Attribution, on_delete=models.CASCADE)
    type_notification = models.CharField(max_length=20, choices=TYPE_CHOICES)
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES)
    duree_emprunt = models.CharField(max_length=10)  # Snapshot de la durée
    destinataire = models.CharField(max_length=200)  # email ou téléphone
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=STATUT_ENVOYEE)
    message_id = models.CharField(max_length=255, blank=True, null=True)
    date_envoi = models.DateTimeField(auto_now_add=True)
    date_scheduled = models.DateTimeField(null=True, blank=True)  # Quand était-ce prévu?
    date_tentative_prochaine = models.DateTimeField(null=True, blank=True)
    erreur_message = models.TextField(blank=True, null=True)
    nb_tentatives = models.IntegerField(default=1)
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-date_envoi']
        indexes = [
            models.Index(fields=['attribution', 'type_notification']),
            models.Index(fields=['statut', 'date_tentative_prochaine']),
        ]
```

---

## Timeline comparée

### 📊 Emprunt court-terme (14h → 18h, 4h)

```
14:00 Création
├─ 14:00 ✉️ EMAIL "Matériel emprunté"
├─ 14:05 💬 WHATSAPP "Confirmé"
│
18:00 Check-in attendu
├─ 18:00 [Monitoring]
├─ 18:30 ⚠️ ALERTE RETARD (si pas retourné)
│        ✉️ EMAIL URGENT
│        💬 WHATSAPP URGENT
│
19:00 [Monitoring]
├─ 19:00 ⚠️ ESCALADE si toujours pas retourné
│
...
```

### 📊 Emprunt moyen-terme (09h lundi → 18h lundi, 9h)

```
09:00 Création (lundi)
├─ 09:00 ✉️ EMAIL "Matériel emprunté"
├─ 09:05 💬 WHATSAPP "Confirmé"
│
16:00 Rappel (2h avant 18h)
├─ 16:00 ✉️ EMAIL "Retour dans 2h"
├─ 16:05 💬 WHATSAPP "Retour 18h?"
│
18:00 Check-in attendu
├─ 18:00 [Monitoring]
├─ 18:30 ⚠️ ALERTE RETARD
│        ✉️ EMAIL URGENT
│        💬 WHATSAPP URGENT
│
...
```

### 📊 Emprunt long-terme (09h lundi → 09h vendredi, 4 jours)

```
09:00 Création (lundi)
├─ 09:00 ✉️ EMAIL "Matériel emprunté - retour vendredi"
├─ 09:05 💬 WHATSAPP "Confirmé"
│
10:00 Mercredi (J-2)
├─ 10:00 ✉️ EMAIL "Rappel: 2 jours restants"
├─ 10:05 💬 WHATSAPP "Rappel J-2"
│
10:00 Jeudi (J-1)
├─ 10:00 ✉️ EMAIL "Rappel: Retour demain!"
├─ 10:05 💬 WHATSAPP "Retour demain?"
│
08:00 Vendredi (Jour retour)
├─ 08:00 ✉️ EMAIL "Rappel final: retour aujourd'hui avant 17h"
├─ 08:05 💬 WHATSAPP "Dernier jour!"
│
09:00 Vendredi
├─ 09:00 [Monitoring]
│
14:00 Vendredi (5h après)
├─ 14:00 ⚠️ ALERTE RETARD
│        ✉️ EMAIL URGENT (Client + Manager)
│        💬 WHATSAPP URGENT
│
...
```

---

## Service NotificationService v2

```python
class NotificationService:
    """Service unifié pour gérer les notifications selon la durée d'emprunt"""
    
    def __init__(self):
        self.email_service = EmailNotificationService()
        self.whatsapp_service = WhatsAppNotificationService()
    
    def on_attribution_created(self, attribution):
        """Déclenché quand une attribution est créée"""
        duree = attribution.duree_emprunt
        
        # Toujours: Notification création
        self._notify(attribution, NotificationLog.TYPE_CREATION)
        
        # Planifier les rappels selon durée
        if duree == Attribution.DUREE_COURT_TERME:
            self._schedule_monitoring_court_terme(attribution)
        
        elif duree == Attribution.DUREE_MOYEN_TERME:
            self._schedule_rappel_2h(attribution)
            self._schedule_monitoring_moyen_terme(attribution)
        
        elif duree == Attribution.DUREE_LONG_TERME:
            self._schedule_rappels_long_terme(attribution)
    
    def _notify(self, attribution, type_notif, canal=None):
        """Envoyer notification immédiate"""
        # Vérifier les préférences
        # Déterminer canaux (email/whatsapp)
        # Envoyer via services appropriés
        pass
    
    def _schedule_rappel_2h(self, attribution):
        """Planifier rappel 2h avant pour moyen terme"""
        rappel_time = datetime.combine(
            attribution.date_retour_prevue,
            attribution.heure_retour_prevue
        ) - timedelta(hours=2)
        
        scheduler.add_job(
            self._notify,
            trigger='date',
            run_date=rappel_time,
            args=[attribution, NotificationLog.TYPE_RAPPEL_2H]
        )
    
    def _schedule_rappels_long_terme(self, attribution):
        """Planifier 3 rappels pour long terme"""
        # J-2 à 10h
        # J-1 à 10h
        # Jour retour à 8h
        pass
    
    def check_overdue_court_terme(self):
        """Appel chaque 15 min pour court terme"""
        attributions = Attribution.objects.filter(
            duree_emprunt=Attribution.DUREE_COURT_TERME,
            date_retour_effective__isnull=True
        )
        
        for attr in attributions:
            prevue = datetime.combine(
                attr.date_retour_prevue,
                attr.heure_retour_prevue
            )
            
            if datetime.now() > prevue + timedelta(minutes=30):
                self._notify(attr, NotificationLog.TYPE_RETARD, urgence=True)
    
    def check_overdue_moyen_terme(self):
        """Appel chaque 30 min pour moyen terme"""
        # Similaire à court terme
        pass
    
    def check_overdue_long_terme(self):
        """Appel quotidien (14h) pour long terme"""
        # Vérifier attributions avec date_retour < aujourd'hui
        # Créer alertes appropriées
        pass
```

---

## Variables d'environnement .env

```bash
# Notifications - Fréquences
NOTIFICATION_CHECK_COURT_TERME_MINUTES=15    # 15 min
NOTIFICATION_CHECK_MOYEN_TERME_MINUTES=30    # 30 min
NOTIFICATION_CHECK_LONG_TERME_HOUR=14        # 14h (quotidien)

# Seuils de retard
NOTIFICATION_RETARD_SEUIL_COURT_TERME=30     # 30 min après heure prévue
NOTIFICATION_RETARD_SEUIL_MOYEN_TERME=60     # 60 min après heure prévue
NOTIFICATION_RETARD_SEUIL_LONG_TERME=14400   # 4h après heure prévue (10h)

# Twilio
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

---

## Résumé des changements modèle

```python
# DANS Attribution:

# AJOUTS:
duree_emprunt = CharField(choices=DUREE_CHOICES)  # AUTO
heure_retour_prevue = TimeField(null=True)        # OPTIONNEL
heure_retour_effective = TimeField(null=True)     # AUTO

# MÉTHODES:
def calculate_duree_emprunt()  # Calcul automatique
def get_notification_schedule() # Retourne tous les rappels planifiés
def check_retard()              # Vérifier si en retard
```

✅ **Avantages:**
- Gestion fine des 3 durées sans code redondant
- Rappels adaptatifs (aucun pour <4h, 1 pour 4-24h, 3+ pour >24h)
- Monitoring adapté à chaque type
- Alertes graduées selon sévérité

