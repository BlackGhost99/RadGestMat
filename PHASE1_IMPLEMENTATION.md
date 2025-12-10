# 📋 PHASE 1 - IMPLÉMENTATION : MODÈLES DE NOTIFICATIONS

**Date:** 9 décembre 2025  
**État:** ✅ COMPLÉTÉE

---

## ✅ Qu'est-ce qui a été fait

### 1️⃣ Modification du modèle `Attribution`

**Fichier:** `assets/models.py`

**Nouveaux champs ajoutés:**
```python
# Durée d'emprunt (auto-calculée)
duree_emprunt = CharField(
    choices=DUREE_CHOICES,  # COURT / MOYEN / LONG
    default=DUREE_LONG_TERME
)

# Heures de retour (pour emprunts < 24h)
heure_retour_prevue = TimeField(null=True, blank=True)
heure_retour_effective = TimeField(null=True, blank=True)
```

**Nouvelles méthodes:**
- `calculate_duree_emprunt()` - Auto-calcul de la durée
- `is_overdue()` - Vérifier si en retard
- `get_retard_minutes()` - Retourner minutes de retard

**Indexes ajoutés:**
- `(duree_emprunt, date_retour_effective)` pour requêtes rapides
- `(date_retour_prevue, duree_emprunt)` pour filtrage par date

---

### 2️⃣ Créer le modèle `NotificationLog`

**Fichier:** `assets/models.py`

**Champs:**
| Champ | Type | Description |
|-------|------|-------------|
| `attribution` | ForeignKey | Lien vers Attribution |
| `type_notification` | CharField | CREATION, RAPPEL_2H, RAPPEL_J_MOINS_2, etc. |
| `canal` | CharField | EMAIL ou WHATSAPP |
| `duree_emprunt` | CharField | Snapshot de la durée au moment d'envoi |
| `destinataire` | CharField | Email ou téléphone |
| `statut` | CharField | ENVOYEE, ECHEC, ECHEC_PERM |
| `message_id` | CharField | ID du provider (Twilio, etc.) |
| `date_envoi` | DateTimeField | Quand a été créée la notification |
| `date_scheduled` | DateTimeField | Quand était prévu l'envoi |
| `date_tentative_prochaine` | DateTimeField | Pour retry |
| `erreur_message` | TextField | Message d'erreur si ECHEC |
| `nb_tentatives` | IntegerField | Nombre de tentatives |

**Indexes:**
- `(attribution, type_notification)` - Pour historique d'une attribution
- `(statut, date_tentative_prochaine)` - Pour retry automatique
- `(date_envoi)` - Pour logs

---

### 3️⃣ Créer le modèle `NotificationPreferences`

**Fichier:** `assets/models.py`

**Champs:**
| Champ | Type | Description |
|-------|------|-------------|
| `user` | OneToOneField | Utilisateur (optionnel) |
| `client` | OneToOneField | Client (optionnel) |
| `notifications_email` | Boolean | Recevoir emails (défaut: True) |
| `notifications_whatsapp` | Boolean | Recevoir WhatsApp (défaut: False) |
| `rappel_j_moins_2` | Boolean | (Long terme) |
| `rappel_j_moins_1` | Boolean | (Long terme) |
| `rappel_final` | Boolean | (Long terme) |
| `rappel_2h_avant` | Boolean | (Moyen terme) |
| `phone_number` | CharField | +33612345678 |
| `date_modification` | DateTimeField | Last change |

**Validation:**
- Soit `user` soit `client` doit être défini
- Si WhatsApp activé → `phone_number` requis

---

### 4️⃣ Créer le modèle `WhatsAppConfig`

**Fichier:** `assets/models.py`

**Champs:**
| Champ | Type | Description |
|-------|------|-------------|
| `api_provider` | CharField | TWILIO (extensible) |
| `api_key` | CharField | Account SID ou équivalent |
| `api_secret` | CharField | Token d'authentification |
| `phone_number_sender` | CharField | Numéro Twilio |
| `is_active` | Boolean | Configuration active (défaut: False) |
| `date_creation` | DateTimeField | When created |
| `date_modification` | DateTimeField | Last change |

**Remarque:** À sécuriser en production (utiliser Django-Environ ou Vault)

---

## 🗄️ Migrations appliquées

**Fichier créé:** `assets/migrations/0007_notificationlog_notificationpreferences_and_more.py`

**Tables créées:**
- `assets_notificationlog` (15 champs + indexes)
- `assets_notificationpreferences` (8 champs)
- `assets_whatsappconfig` (7 champs)

**Modifications:**
- 3 champs ajoutés à `assets_attribution` (duree_emprunt, heure_retour_prevue, heure_retour_effective)
- 2 indexes créés sur `assets_attribution`

**Résultat:** ✅ Migrations appliquées avec succès (0007_...)

---

## 🛠️ Admin Django enregistré

**Fichier modifié:** `assets/admin.py`

### NotificationLogAdmin
- **List display:** id, attribution, type_notification, canal, statut, date_envoi, nb_tentatives
- **Filters:** type_notification, canal, statut, date_envoi, duree_emprunt
- **Readonly:** date_envoi, attribution
- **Permissions:** 
  - ❌ Pas d'ajout manuel (auto-créées)
  - ❌ Pas de suppression (audit trail)

### NotificationPreferencesAdmin
- **List display:** destinataire, notifications_email, notifications_whatsapp
- **Search:** user, client, phone_number
- **Fieldsets:** Destinataire, Canaux, Rappels

### WhatsAppConfigAdmin
- **List display:** api_provider, phone_number_sender, is_active
- **Credentials:** Collapsible (⚠️ À sécuriser)

---

## 📊 Classification des emprunts - Récapitulatif

```
COURT TERME (0-4h)
├─ Rappels: AUCUN
├─ Monitoring: Chaque 15 min
└─ Alerte retard: Si > 30 min après heure prévue

MOYEN TERME (4h-24h)
├─ Rappels: 1 (2h avant)
├─ Monitoring: Chaque 30 min
└─ Alerte retard: Si > 60 min après heure prévue

LONG TERME (>24h)
├─ Rappels: 3 (J-2, J-1, jour retour)
├─ Monitoring: Quotidien (14h)
└─ Alerte retard: Si > 10h du jour retour
```

---

## 🔄 Workflow automatique de `calculate_duree_emprunt()`

```python
def save(self, *args, **kwargs):
    # Auto-calculer la durée d'emprunt
    self.duree_emprunt = self.calculate_duree_emprunt()
    
    if not self.pk:
        # Première sauvegarde
        self.materiel.statut_disponibilite = Materiel.STATUT_ATTRIBUE
        self.materiel.save()
    
    super().save(*args, **kwargs)
```

**Exemple:**
```
Attribution créée le 2025-12-09 14:00
date_retour_prevue = 2025-12-09
heure_retour_prevue = 18:00
→ delta = 4 heures
→ duree_emprunt = 'COURT' ✓
```

---

## 📝 Méthodes utiles sur Attribution

### `is_overdue()`
Retourne `True` si l'attribution est en retard:
```python
attr = Attribution.objects.get(id=1)
if attr.is_overdue():
    print(f"En retard de {attr.get_retard_minutes()} minutes")
```

### `get_retard_minutes()`
Retourne le nombre de minutes de retard:
```python
if attr.duree_emprunt in ['COURT', 'MOYEN']:
    # Basé sur heure_retour_prevue
    retard_min = attr.get_retard_minutes()
else:
    # Basé sur date_retour_prevue (10h00)
    retard_min = attr.get_retard_minutes()
```

---

## 🧪 Tester avec Django Shell

```bash
# Activer Python shell
python manage.py shell

# Importer les modèles
from assets.models import Attribution, NotificationLog, NotificationPreferences, WhatsAppConfig
from django.utils import timezone
from datetime import datetime, timedelta

# Créer une attribution de test
attr = Attribution.objects.create(
    materiel_id=1,
    client_id=1,
    departement_id=1,
    employe_responsable_id=1,
    date_retour_prevue='2025-12-09',
    heure_retour_prevue='18:00'
)

# Vérifier la durée calculée
print(f"Durée: {attr.duree_emprunt}")  # COURT
print(f"En retard: {attr.is_overdue()}")  # False

# Vérifier NotificationLog (après création)
logs = NotificationLog.objects.filter(attribution=attr)
print(f"Logs: {logs.count()}")

# Vérifier NotificationPreferences
prefs = NotificationPreferences.objects.filter(user_id=1)
print(f"Preferences: {prefs.exists()}")

# Vérifier WhatsAppConfig
config = WhatsAppConfig.objects.first()
print(f"Config active: {config.is_active if config else 'None'}")
```

---

## 🚀 Prochaines étapes (Phase 2+)

### Phase 2: Service d'Email
- [ ] Créer `EmailNotificationService` dans `assets/services.py`
- [ ] Écrire templates HTML pour 7 types de notifications
- [ ] Intégrer avec Django email backend
- [ ] Tester avec MailHog ou service de test

### Phase 3: Signaux Django
- [ ] Signal `post_save(Attribution)` pour création notification
- [ ] Signal `post_save(HistoriqueAttribution)` pour check-in
- [ ] Auto-créer `NotificationLog` entries

### Phase 4: APScheduler
- [ ] Setup APScheduler dans Django
- [ ] Scheduler pour rappels J-2, J-1, jour retour
- [ ] Scheduler pour monitoring retards
- [ ] Gestion cron/job worker

### Phase 5: WhatsApp + Twilio
- [ ] Setup compte Twilio
- [ ] Implémenter `WhatsAppNotificationService`
- [ ] Test avec sandbox WhatsApp
- [ ] Fallback à email si WhatsApp échoue

### Phase 6: Dashboard
- [ ] Administrateur: Vue NotificationLog
- [ ] User: Gestion préférences
- [ ] Test page pour trigger notifications
- [ ] Historique/audit notifications

---

## 📋 Checklist

- ✅ Modèle `Attribution` modifié (3 champs, 2 méthodes)
- ✅ Modèle `NotificationLog` créé (audit trail)
- ✅ Modèle `NotificationPreferences` créé (user/client prefs)
- ✅ Modèle `WhatsAppConfig` créé (Twilio config)
- ✅ Migrations créées et appliquées (#0007)
- ✅ Admin Django enregistré (3 classes)
- ✅ Indexes créés pour performance
- ✅ Validation (NotificationPreferences)

---

## 📚 Documentation générée

- ✅ `NOTIFICATION_DURATIONS.md` - Classification et timelines
- ✅ `NOTIFICATION_ARCHITECTURE.md` - Diagrammes ASCII
- ✅ `PHASE1_IMPLEMENTATION.md` - Ce fichier (récap détaillé)

---

## 🔗 Fichiers modifiés

```
assets/
├── models.py            [+150 lignes - 3 modèles + modifications Attribution]
├── admin.py             [+90 lignes - 3 classes admin]
└── migrations/
    └── 0007_...py       [AUTO - Django]
```

**Total lignes:** ~240 nouvelles lignes de production

---

## ⚡ Performance

### Indexes créés
- `assets_attr_duree_e_00718e_idx` - Pour filtrer par durée
- `assets_attr_date_re_59c8ef_idx` - Pour filtrer par date
- `assets_noti_attribu_d84cd3_idx` - Pour requête Attribution → Logs
- `assets_noti_statut_29bbf0_idx` - Pour retry automatique
- `assets_noti_date_en_7af5e1_idx` - Pour logs par date

### Queries optimisées
```python
# Trouver attributions court-terme en retard
Attribution.objects.filter(
    duree_emprunt='COURT',
    date_retour_effective__isnull=True
)  # ← Utilise index (duree_emprunt, date_retour_effective)

# Trouver notifications à renvoyer
NotificationLog.objects.filter(
    statut='ECHEC',
    date_tentative_prochaine__lt=timezone.now()
)  # ← Utilise index (statut, date_tentative_prochaine)
```

---

**Phase 1 Complétée ✅**  
**Prêt pour Phase 2 (Email Service)**

