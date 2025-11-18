# RadGestMat - Plateforme de Gestion des Actifs Hôteliers

## Vue d'ensemble

RadGestMat est une plateforme Django complète pour la gestion des actifs (matériel, équipements) d'un établissement hôtelier, développée selon les spécifications du **Cahier des Charges - Plateforme de Gestion des Actifs Hôteliers**.

## ✅ Fonctionnalités implémentées (Phase 1)

### Modèles de données
- **Departement** : Gestion des départements
- **Categorie** : Catégorisation du matériel par département
- **Materiel** : Gestion complète du matériel avec:
  - Asset ID unique et numéro d'inventaire
  - État technique (FONCTIONNEL/DEFECTUEUX/EN_MAINTENANCE)
  - Statut de disponibilité (DISPONIBLE/ATTRIBUE/MAINTENANCE/HORS_SERVICE)
  - Génération automatique de codes QR
  - Données financières (date d'achat, prix)
- **Client** : Gestion des clients (hébergement, conférence, interne)
- **Attribution** : Suivi des prêts de matériel
- **HistoriqueAttribution** : Audit trail complet
- **Alerte** : Système d'alertes (retards, défauts, stock critique)
- **ProfilUtilisateur** : Extension du profil utilisateur avec rôles

### Interface d'administration Django
- Dashboard complet avec statistiques
- Enregistrement de tous les modèles dans l'admin
- Fieldsets organisés et filtres avancés
- Actions personnalisées (ex: marquer comme réglementé)

### Interface utilisateur
- Authentification (login/logout)
- Dashboard avec statistiques des actifs
- **Liste du matériel** avec:
  - Recherche multi-critères
  - Filtrage par statut, état technique, catégorie
  - Affichage des statuts avec badges
  - Actions rapides (voir, modifier, supprimer)
- **Création de matériel**
  - Formulaire complet
  - Génération automatique du QR code
  - Validation des données
- **Modification de matériel**
- **Suppression de matériel** avec confirmation
- **Vue détails** du matériel avec historique

### Infrastructure technique
- Django 5.2.8
- Python 3.14.0
- SQLite3
- Bootstrap 5.3
- QR Code génération automatique

## Installation et démarrage

### Prérequis
- Python 3.14+
- Django 5.2.8

### Installation

```bash
# Clone du projet
cd RadGestMat

# Installation des dépendances
pip install django==5.2.8 qrcode[pil] python-decouple

# Application des migrations
python manage.py migrate

# Création d'un superutilisateur
python manage.py createsuperuser
# Email: admin@hotel.com
# Mot de passe: admin123

# Création de données de test
python create_test_data.py

# Démarrage du serveur
python manage.py runserver 0.0.0.0:8000
```

### Accès

- **Dashboard** : http://localhost:8000/
- **Admin Django** : http://localhost:8000/admin/
- **Liste Matériel** : http://localhost:8000/materiel/
- **Identifiants test** : admin / admin123

## Structure du projet

```
RadGestMat/
├── assets/
│   ├── models.py          # Modèles de données
│   ├── views.py           # Vues (dashboard, CRUD matériel)
│   ├── admin.py           # Configuration admin Django
│   ├── forms.py           # Formulaires
│   ├── urls.py            # Routes URL
│   └── migrations/        # Migrations de base de données
├── users/
│   ├── models.py          # Modèle ProfilUtilisateur
│   ├── admin.py           # Configuration admin utilisateur
│   └── context_processors.py
├── radgestmat/
│   ├── settings.py        # Configuration Django
│   ├── urls.py            # Routes principales
│   ├── wsgi.py            # Configuration WSGI
│   └── middleware.py      # Middleware personnalisé
├── templates/
│   ├── base.html          # Template de base
│   ├── login.html         # Page de connexion
│   ├── assets/
│   │   ├── dashboard.html
│   │   ├── materiel_list.html
│   │   ├── materiel_form.html
│   │   ├── materiel_detail.html
│   │   └── materiel_confirm_delete.html
├── static/                # Ressources statiques
├── manage.py              # Script de gestion Django
└── create_test_data.py    # Script de données de test
```

## Utilisation

### Connexion
1. Accédez à http://localhost:8000/
2. Connectez-vous avec : admin / admin123

### Gestion du matériel

#### Voir la liste du matériel
- URL : http://localhost:8000/materiel/
- Filtrez par : recherche, statut, état technique, catégorie

#### Ajouter du matériel
1. Cliquez sur "Ajouter du matériel"
2. Remplissez le formulaire
3. Le QR code est généré automatiquement à la sauvegarde

#### Modifier du matériel
1. Cliquez sur l'icône "Modifier" dans la liste
2. Modifiez les informations
3. Sauvegardez

#### Supprimer du matériel
1. Cliquez sur l'icône "Supprimer"
2. Confirmez la suppression

### Admin Django

#### Accès
- URL : http://localhost:8000/admin/
- Identifiants : admin / admin123

#### Gestion avancée
- Création/modification de départements
- Gestion des catégories
- Attributions de matériel
- Historique complet des actions
- Gestion des alertes
- Configuration des profils utilisateur

## 📋 Prochaines phases (Phase 2)

### À implémenter
- ✅ **CRUD Matériel** (implémenté)
- ⏳ **CRUD Clients** (à compléter)
- ⏳ **Workflows Check-out/Check-in**
  - Scanner QR code
  - Vérification de disponibilité
  - Enregistrement des attributions
  - Retour de matériel
- ⏳ **Système de permissions** avancé
- ⏳ **Dashboards supplémentaires**
  - Rapport d'activité
  - Analyse de l'inventaire
  - Suivi des alertes
- ⏳ **API REST** pour mobile
- ⏳ **Export de données** (PDF, Excel)
- ⏳ **Notifications** (email, SMS)

## Modèle de données

```
Departement (1) ──→ (N) Categorie
     │
     └──→ (N) Materiel
           │
           └──→ (N) Attribution ←─ (1) Client
                    │
                    └──→ (N) HistoriqueAttribution
                    
ProfilUtilisateur ←─ (1) User
        │
        └──→ (1) Departement
```

## API des vues

### Vues implémentées

#### Dashboard
```
GET /
```
- Affiche les statistiques d'actifs
- Historique des attributions récentes

#### Liste matériel
```
GET /materiel/
GET /materiel/?q=recherche&statut=DISPONIBLE&etat=FONCTIONNEL
```
- Liste paginée avec filtres
- Recherche multi-critères

#### Création matériel
```
GET /materiel/ajouter/      (formulaire)
POST /materiel/ajouter/     (sauvegarde)
```

#### Détails matériel
```
GET /materiel/<id>/
```

#### Modification matériel
```
GET /materiel/<id>/modifier/      (formulaire)
POST /materiel/<id>/modifier/     (sauvegarde)
```

#### Suppression matériel
```
GET /materiel/<id>/supprimer/     (confirmation)
POST /materiel/<id>/supprimer/    (suppression)
```

## Configurations

### Settings.py
```python
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'assets:dashboard'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'assets',
]
```

### Variables d'environnement (optionnel)
```
DEBUG=True
SECRET_KEY=votre_clé_secrète
DATABASE_URL=sqlite:///db.sqlite3
```

## Statuts et états

### État technique
- `FONCTIONNEL` : L'équipement fonctionne normalement
- `DEFECTUEUX` : L'équipement a un problème
- `EN_MAINTENANCE` : L'équipement est en réparation

### Statut de disponibilité
- `DISPONIBLE` : L'équipement est disponible pour attribution
- `ATTRIBUE` : L'équipement a été prêté
- `MAINTENANCE` : L'équipement en maintenance
- `HORS_SERVICE` : L'équipement n'est pas utilisable

### Types de client
- `HEBERGEMENT` : Chambre d'hôtel
- `CONFERENCE` : Salle de conférence
- `INTERNE` : Service interne

### Rôles utilisateur
- `SUPER_ADMIN` : Administrateur système
- `MANAGER_DEPT` : Responsable de département
- `UTILISATEUR_STANDARD` : Utilisateur standard

## Support et documentation

- Documentation Django : https://docs.djangoproject.com/
- Bootstrap : https://getbootstrap.com/docs/5.3/
- qrcode : https://github.com/lincolnloop/python-qrcode

---

**Version** : 1.0.0 - Phase 1 MVP  
**Date** : Novembre 2024  
**Auteur** : Équipe RadGestMat
