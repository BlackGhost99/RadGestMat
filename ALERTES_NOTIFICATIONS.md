# Système d'Alertes et Notifications - RadGestMat

## Vue d'ensemble

Le système d'alertes et notifications permet de détecter automatiquement et de notifier les utilisateurs des situations nécessitant une attention particulière dans la gestion du matériel.

## Types d'Alertes

### 1. Retard de retour
- **Déclenchement**: Lorsqu'une attribution dépasse la date de retour prévue
- **Sévérité**: 
  - `WARNING` si retard < 7 jours
  - `CRITICAL` si retard ≥ 7 jours
- **Détection**: Automatique lors de l'exécution de la détection

### 2. Matériel défectueux
- **Déclenchement**: Lorsqu'un matériel a l'état technique `DEFECTUEUX` et est disponible ou attribué
- **Sévérité**: `WARNING`
- **Détection**: Automatique lors de l'exécution de la détection

### 3. Stock critique
- **Déclenchement**: Lorsqu'un équipement (par nom) a moins de 2 unités disponibles
- **Sévérité**: `WARNING`
- **Seuil configurable**: Modifiable dans `AlerteService.SEUIL_STOCK_CRITIQUE` (par défaut: 2)
- **Détection**: Automatique lors de l'exécution de la détection
- **Exemple**: Si vous avez 7 projecteurs vidéo et qu'il n'en reste que 2 disponibles, une alerte sera créée
- **Logique**: Le système groupe les matériels par nom d'équipement et département, puis vérifie le nombre d'unités disponibles (statut DISPONIBLE et état FONCTIONNEL)

### 4. Matériel perdu
- **Déclenchement**: Lorsqu'une attribution n'a pas été retournée après 30 jours de la date de retour prévue
- **Sévérité**: `CRITICAL`
- **Délai configurable**: Modifiable dans `AlerteService.JOURS_AVANT_ALERTE_PERDU`
- **Détection**: Automatique lors de l'exécution de la détection

## Canaux de Notification

### 1. Interface Utilisateur

#### Badges dans la Navigation
- Un badge affiche le nombre d'alertes non réglées dans le menu "Alertes"
- Le badge est rouge si des alertes critiques existent, jaune sinon

#### Dashboard
- Section "Alertes récentes" affichant les 5 dernières alertes
- Indicateurs visuels de sévérité (rouge, jaune, bleu)

#### Page Liste des Alertes
- Vue complète de toutes les alertes non réglées
- Filtres par type et sévérité
- Statistiques en temps réel

### 2. Email

#### Alertes Critiques
- Envoi automatique d'email aux managers du département concerné
- Déclenché lors de la création d'une alerte critique
- Contenu: détails de l'alerte, matériel concerné, client, liens vers l'application

#### Rapports Quotidiens
- Envoi quotidien aux managers avec:
  - Statistiques des alertes
  - Top 10 des alertes récentes
  - Répartition par type
- Commande: `python manage.py rapport_alertes_quotidien`

### 3. Rapports Quotidiens

#### Commande de Gestion
```bash
# Envoyer les rapports à tous les départements
python manage.py rapport_alertes_quotidien

# Envoyer pour un département spécifique
python manage.py rapport_alertes_quotidien --departement=1

# Mode test (affiche sans envoyer)
python manage.py rapport_alertes_quotidien --test
```

#### Planification (Cron)
Pour automatiser l'envoi quotidien, ajouter dans crontab:
```bash
# Envoyer le rapport tous les jours à 8h00
0 8 * * * cd /chemin/vers/projet && python manage.py rapport_alertes_quotidien
```

## Utilisation

### Détection Manuelle des Alertes

1. Accéder à la page "Alertes" dans le menu
2. Cliquer sur "Détecter les alertes"
3. Le système va:
   - Détecter tous les retards
   - Détecter les matériels défectueux
   - Détecter les stocks critiques
   - Détecter les matériels perdus
   - Envoyer des emails pour les alertes critiques

### Marquer une Alerte comme Réglée

1. Accéder à la page de détails de l'alerte
2. Cliquer sur "Marquer comme réglée"
3. Confirmer l'action

### Configuration Email

Dans `settings.py`:
```python
# Développement (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Production (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@gmail.com'
EMAIL_HOST_PASSWORD = 'votre-mot-de-passe'
DEFAULT_FROM_EMAIL = 'RadGestMat <noreply@votre-domaine.com>'
SITE_URL = 'https://votre-domaine.com'  # Pour les liens dans les emails
```

## Structure Technique

### Fichiers Principaux

- `assets/services.py`: Service de détection des alertes
- `assets/email_service.py`: Service d'envoi d'emails
- `assets/views.py`: Vues pour l'interface des alertes
- `assets/signals.py`: Signaux pour l'envoi automatique d'emails
- `assets/context_processors.py`: Context processor pour les badges
- `assets/management/commands/rapport_alertes_quotidien.py`: Commande de gestion

### Modèles

- `Alerte`: Modèle principal pour les alertes
  - `type_alerte`: Type d'alerte (RETARD, DEFECTUEUX, STOCK_CRITIQUE, PERDU)
  - `severite`: Sévérité (INFO, WARNING, CRITICAL)
  - `reglementee`: Statut (True si réglée)

## Personnalisation

### Modifier les Seuils

Dans `assets/services.py`:
```python
class AlerteService:
    JOURS_AVANT_ALERTE_RETARD = 0  # Alerte dès le jour de la date de retour
    JOURS_AVANT_ALERTE_PERDU = 30  # Matériel considéré perdu après 30 jours
    SEUIL_STOCK_CRITIQUE = 2  # Moins de 2 unités disponibles = stock critique (par nom d'équipement)
```

**Note sur le stock critique**: Le système détecte les stocks critiques en groupant les matériels par **nom d'équipement** (pas par catégorie). Par exemple, si vous avez plusieurs "Projecteur vidéo" avec le même nom, le système comptera le total et vérifiera combien sont disponibles. Si le nombre disponible atteint le seuil (par défaut 2), une alerte sera créée.

### Désactiver l'Envoi Automatique d'Emails

Dans `assets/services.py`, méthode `detecter_toutes_alertes`:
```python
resultats = AlerteService.detecter_toutes_alertes(envoyer_emails=False)
```

## Tests

Pour tester le système:
1. Créer des attributions avec dates de retour dépassées
2. Marquer des matériels comme défectueux
3. Réduire le stock disponible d'une catégorie
4. Exécuter la détection manuellement
5. Vérifier les emails dans la console (mode développement)

