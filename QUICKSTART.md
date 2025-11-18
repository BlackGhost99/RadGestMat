# 🚀 QUICK START - RadGestMat

## ⚡ 5 Minutes pour Démarrer

### 1️⃣ Installation (2 min)

```bash
# Aller au dossier
cd RadGestMat

# Installer les dépendances
pip install django==5.2.8 qrcode[pil] python-decouple

# Appliquer les migrations
python manage.py migrate

# Charger les données de test
python create_test_data.py
```

### 2️⃣ Démarrer le serveur (30 sec)

```bash
python manage.py runserver 0.0.0.0:8000
```

### 3️⃣ Accéder à l'application (30 sec)

- **Dashboard:** http://localhost:8000/
- **Matériel:** http://localhost:8000/materiel/
- **Admin:** http://localhost:8000/admin/

### 4️⃣ Se connecter (1 min)

**Identifiants:**
- Username: `admin`
- Password: `admin123`

### 5️⃣ Tester les fonctionnalités (1 min 30)

✅ Voir la liste du matériel
✅ Créer un nouveau matériel
✅ Filtrer par statut/catégorie
✅ Voir les détails
✅ Modifier
✅ Supprimer avec confirmation

---

## 📊 Ce Qui Fonctionne

```
✅ Dashboard avec statistiques
✅ Authentification (Login/Logout)
✅ Liste du matériel avec filtres
✅ Création de matériel (QR code auto)
✅ Modification de matériel
✅ Suppression de matériel
✅ Admin Django complet
✅ Données de test pré-chargées
✅ Design responsive Bootstrap
```

---

## 🎮 Cas d'Usage Typique

### 1. Ajouter un matériel
```
Dashboard → "Ajouter du matériel"
  → Remplir formulaire
  → Soumettre
  → QR code généré automatiquement ✨
```

### 2. Chercher un matériel
```
Matériel → Barre de recherche
  → Taper "ordinateur"
  → Résultats affichés
```

### 3. Filtrer par statut
```
Matériel → Dropdown "Statut"
  → Sélectionner "DISPONIBLE"
  → Appliquer → Résultats filtrés
```

### 4. Voir les détails
```
Matériel → Cliquer "Voir"
  → Page détails
  → Info complète + historique
```

### 5. Modifier
```
Détails → Bouton "Modifier"
  → Formulaire pré-rempli
  → Changer champs
  → Soumettre
```

### 6. Supprimer
```
Liste/Détails → Bouton "Supprimer"
  → Page de confirmation
  → Confirmer suppression
  → ✅ Supprimé
```

---

## 📁 Structure Rapide

```
RadGestMat/
├── manage.py              # CLI Django
├── db.sqlite3             # Base de données
├── create_test_data.py    # Données de test
├── README.md              # Doc complète
├── CHANGELOG.md           # Changements
├── DEPLOYMENT_REPORT.md   # Rapport
├── PRODUCTION_DEPLOYMENT.md  # Prod guide
├── assets/                # App principale
│   ├── models.py          # Modèles
│   ├── views.py           # Vues
│   ├── forms.py           # Formulaires
│   ├── admin.py           # Admin Django
│   └── urls.py            # Routes
├── users/                 # App utilisateurs
│   ├── models.py
│   └── admin.py
├── templates/             # Templates HTML
│   ├── base.html
│   └── assets/
│       ├── dashboard.html
│       ├── materiel_list.html
│       ├── materiel_form.html
│       ├── materiel_detail.html
│       └── materiel_confirm_delete.html
└── static/                # CSS/JS/Images
```

---

## 🔧 Commandes Utiles

```bash
# Démarrer le serveur
python manage.py runserver

# Créer superutilisateur
python manage.py createsuperuser

# Charger données test
python create_test_data.py

# Exécuter tests
python manage.py test assets.tests

# Migrations
python manage.py makemigrations
python manage.py migrate

# Nettoyer
python manage.py flush  # ⚠️ Efface TOUT

# Shell Django
python manage.py shell
```

---

## 🎯 Fichiers Clés

| Fichier | Purpose |
|---------|---------|
| `assets/models.py` | 8 modèles de données |
| `assets/views.py` | 6 vues CRUD + dashboard |
| `assets/admin.py` | 7 ModelAdmin classes |
| `assets/forms.py` | MaterielForm |
| `README.md` | Documentation complète |
| `create_test_data.py` | Population DB |
| `CHANGELOG.md` | Version history |

---

## ⚙️ Configuration Rapide

### Variables d'environnement (optionnel)

Créer `.env`:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
```

Puis charger:
```python
from decouple import config
DEBUG = config('DEBUG', default=True, cast=bool)
```

---

## 🐛 Problèmes Courants

### ❌ "ModuleNotFoundError: No module named 'qrcode'"
```bash
pip install qrcode[pil]
```

### ❌ "Port 8000 is already in use"
```bash
python manage.py runserver 8001
# ou
lsof -ti:8000 | xargs kill -9
```

### ❌ "No such table: assets_materiel"
```bash
python manage.py migrate
```

### ❌ "Cannot find superuser"
```bash
python manage.py createsuperuser
# puis: admin / admin123
```

---

## 🔄 Workflow Complet

```
1. npm install Django
   ↓
2. python manage.py migrate
   ↓
3. python create_test_data.py
   ↓
4. python manage.py runserver
   ↓
5. http://localhost:8000/ (login: admin/admin123)
   ↓
6. Test toutes les fonctionnalités
   ↓
7. ✨ Application prête!
```

---

## 📚 Prochaines Étapes

Après avoir testé:

1. **Lire la documentation complète**: `README.md`
2. **Voir le rapport**: `DEPLOYMENT_REPORT.md`
3. **Préparer production**: `PRODUCTION_DEPLOYMENT.md`
4. **Implémenter Phase 2**: Workflows check-in/out
5. **Ajouter utilisateurs réels**: Admin → Users

---

## 📞 Besoin d'Aide?

- ✅ Documentation: `README.md`
- ✅ Troubleshooting: `PRODUCTION_DEPLOYMENT.md`
- ✅ Changements: `CHANGELOG.md`
- ✅ Report: `DEPLOYMENT_REPORT.md`

---

## 🎉 C'est Prêt!

L'application est **100% fonctionnelle** et prête à:
- ✅ Tests
- ✅ Déploiement
- ✅ Développement Phase 2
- ✅ Production

**Version:** 1.0.0 MVP
**Status:** Production Ready ✅
**Date:** Novembre 2024

Bon courage! 🚀
