# 🚀 Guide de Démarrage Rapide - Système de Notifications

## ✅ Phases Complétées

- ✅ **Phase 1**: Modèles de données (NotificationLog, NotificationPreferences, WhatsAppConfig)
- ✅ **Phase 2**: Service Email avec 7 templates HTML
- ✅ **Phase 3**: Signaux Django pour notifications automatiques
- ✅ **Phase 4**: APScheduler avec 5 jobs automatisés
- ✅ **Phase 5**: WhatsApp/Twilio intégration (TESTÉ ✅)
- ✅ **Phase 6**: Dashboard Admin avec statistiques et préférences

---

## 🎯 Fonctionnalités Actives

### Notifications Automatiques (Phase 3)

#### ✉️ À la création d'une attribution:
```python
attribution = Attribution.objects.create(
    materiel=mon_materiel,
    client=mon_client,
    # ... autres champs
)
# → Email + WhatsApp envoyés automatiquement selon préférences utilisateur
```

#### 📦 Au retour du matériel:
```python
attribution.date_retour_effective = date.today()
attribution.save()
# → Confirmation Email + WhatsApp envoyées automatiquement
```

### Rappels Programmés (Phase 4)

Le scheduler APScheduler envoie automatiquement:

| Type | Quand | Fréquence |
|------|-------|-----------|
| Rappel J-2 | 2 jours avant | Toutes les heures à 09:00 |
| Rappel J-1 | 1 jour avant | Toutes les heures à 09:00 |
| Rappel Final | Jour du retour | Toutes les heures à 08:00 |
| Rappel 2h | 2h avant (moyen terme) | Toutes les 30 min |
| Alerte Retard | Matériel en retard | Toutes les heures à 10:00 |

### Dashboard Admin (Phase 6)

- 📊 **Dashboard**: http://127.0.0.1:8000/notifications/dashboard/
  - Statistiques globales
  - Historique des notifications
  - Taux de succès

- ⚙️ **Préférences**: http://127.0.0.1:8000/notifications/preferences/
  - Choix Email/WhatsApp
  - Configuration rappels
  - Numéro WhatsApp

---

## 🔧 Configuration Rapide

### 1. Vérifier la Migration

```bash
python manage.py migrate
```

Devrait afficher:
```
Operations to perform:
  Apply all migrations: admin, assets, auth, contenttypes, sessions, users
Running migrations:
  No migrations to apply.
```

### 2. Créer un Super Utilisateur (si nécessaire)

```bash
python manage.py createsuperuser
```

### 3. Lancer le Serveur

```bash
cd C:\Users\BlackGhost\Desktop\RadGestMat\RadGestMat
.\env_new\Scripts\python.exe manage.py runserver
```

### 4. Lancer le Scheduler (Terminal séparé)

```bash
cd C:\Users\BlackGhost\Desktop\RadGestMat\RadGestMat
.\env_new\Scripts\python.exe manage.py run_scheduler
```

---

## 🧪 Tests Rapides

### Test 1: Notifications Automatiques

```bash
python scripts/test_notifications_complete.py
```

**Ce test va**:
1. Créer une attribution de test
2. Déclencher les signaux de création (Email + WhatsApp)
3. Marquer le retour
4. Déclencher les signaux de restitution
5. Afficher les statistiques

**Résultat attendu**:
```
✅ TESTS TERMINÉS
✓ Signaux Django configurés
✓ Notification de création: True
✓ Notification de restitution: True
✓ Dashboard accessible
```

### Test 2: WhatsApp Direct

```bash
python scripts/test_whatsapp_final.py
```

**Résultat attendu**:
```
✅ Message envoyé avec succès!
   Message SID: SMxxxxxxxxx
   Status: queued
   To: +24105339274
```

---

## 📱 Configuration WhatsApp (Déjà Fait ✅)

Les credentials Twilio sont déjà configurés dans `radgestmat/settings/development.py`:

```python
TWILIO_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_AUTH_TOKEN = '13b60d7e45cfdbd28b7cd9f9d0c7e3d1'
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'
```

**Téléphone de test**: +24105339274

**Note**: Sandbox Twilio actif et vérifié ✅

---

## 🎨 Interface Utilisateur

### Admin Django

http://127.0.0.1:8000/admin/

**Modèles disponibles**:
- `NotificationLog` - Historique complet
- `NotificationPreferences` - Préférences utilisateurs
- `WhatsAppConfig` - Configuration Twilio

### Dashboard Notifications

http://127.0.0.1:8000/notifications/dashboard/

**Statistiques affichées**:
- Total notifications envoyées
- Taux de succès
- Répartition Email/WhatsApp
- Distribution par type
- 50 dernières notifications

**Permissions**: Super Admin et Managers uniquement

### Mes Préférences

http://127.0.0.1:8000/notifications/preferences/

**Options**:
- ✅/❌ Notifications Email
- ✅/❌ Notifications WhatsApp
- 📞 Numéro WhatsApp
- ✅/❌ Rappel J-2, J-1, Final, 2h

**Permissions**: Tous utilisateurs connectés

---

## 📝 Utilisation Quotidienne

### Scénario 1: Attribution d'un matériel

1. Admin crée une attribution via l'interface
2. **Automatique**: Email + WhatsApp de confirmation envoyés au client
3. `NotificationLog` créé pour traçabilité

### Scénario 2: Rappels automatiques

1. Le scheduler tourne en arrière-plan
2. **Automatique**: Vérifie les attributions à rappeler
3. **Automatique**: Envoie les rappels selon le type d'emprunt
4. Logs créés pour chaque envoi

### Scénario 3: Retour de matériel

1. Admin marque l'attribution comme retournée
2. **Automatique**: Confirmation Email + WhatsApp envoyées
3. Client reçoit récapitulatif du retour

### Scénario 4: Gestion des préférences

1. Utilisateur se connecte
2. Accède à `/notifications/preferences/`
3. Active/désactive canaux
4. Configure numéro WhatsApp
5. Sauvegarde → Notifications futures respectent les préférences

---

## 🔍 Debugging

### Vérifier les Logs

#### Django (console)
Les emails s'affichent dans la console du serveur Django

#### Notifications Log (database)
```python
from assets.models import NotificationLog

# Dernières notifications
NotificationLog.objects.order_by('-date_envoi')[:10]

# Notifications échouées
NotificationLog.objects.filter(statut='ECHEC_PERM')

# Par canal
NotificationLog.objects.filter(canal='WHATSAPP')
```

#### Scheduler Log
```bash
tail -f logs/scheduler.log
```

### Problèmes Courants

#### ❌ Pas de notifications à la création

**Vérifier**:
1. Signaux activés: `assets/apps.py` contient `import assets.signals`
2. Préférences utilisateur: Email/WhatsApp activés?
3. Logs Django: Erreurs affichées?

**Solution**:
```bash
python scripts/test_notifications_complete.py
```

#### ❌ WhatsApp non reçu

**Vérifier**:
1. Sandbox Twilio rejoint? (envoyer `join <code>`)
2. Numéro correct: +24105339274
3. Credentials valides dans settings
4. Check Twilio Console: https://console.twilio.com/

**Solution**:
```bash
python scripts/test_whatsapp_final.py
```

#### ❌ Scheduler ne démarre pas

**Vérifier**:
1. APScheduler installé: `pip list | grep APScheduler`
2. Pas d'autre instance en cours: `ps aux | grep scheduler`

**Solution**:
```bash
python manage.py run_scheduler
```

---

## 📊 Monitoring en Production

### Métriques Clés

1. **Taux de succès**: > 95%
2. **Délai d'envoi**: < 5 secondes
3. **Jobs scheduler**: Exécution sans erreur

### Alerting

Configurer alertes pour:
- Taux d'échec > 10%
- Scheduler arrêté
- Twilio quota dépassé
- Base de données full

### Maintenance

- Purger `NotificationLog` > 90 jours
- Vérifier quotas Twilio
- Monitorer temps de réponse
- Backup base de données

---

## 📞 Support

### Documentation Complète

Voir `NOTIFICATIONS_COMPLETE.md` pour:
- Architecture détaillée
- Code source complet
- Configuration avancée
- Déploiement production

### Ressources

- Django Signals: https://docs.djangoproject.com/en/5.0/topics/signals/
- APScheduler: https://apscheduler.readthedocs.io/
- Twilio WhatsApp: https://www.twilio.com/docs/whatsapp
- Twilio Console: https://console.twilio.com/

### Contacts

- Email: support@radgestmat.com
- GitHub: https://github.com/BlackGhost99/RadGestMat

---

## ✅ Checklist Déploiement

- [x] Migration 0007 appliquée
- [x] Serveur Django opérationnel
- [x] Signaux activés et testés
- [x] WhatsApp Twilio configuré et testé ✅
- [x] Email backend configuré
- [x] Dashboard accessible
- [x] Préférences modifiables
- [ ] Scheduler en arrière-plan (à lancer)
- [ ] Monitoring configuré
- [ ] Backup automatique configuré

---

**Status**: ✅ Système Complet et Opérationnel  
**Version**: 1.0.0  
**Date**: 10 Décembre 2025
