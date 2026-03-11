# 🚀 DÉPLOIEMENT RAPIDE - RadGestMat

## Configuration pour: **10.105.42.118** (LBVH.rezidor.com)

### 📋 TL;DR - 3 étapes

#### 1️⃣ Copier le projet
```bash
# Sur serveur 10.105.42.118
cd /opt/radgestmat
# Copier tous les fichiers RadGestMat ici
```

#### 2️⃣ Lancer le déploiement
```bash
# Linux/WSL:
bash deploy.sh

# Windows PowerShell:
.\deploy.ps1
```

#### 3️⃣ Créer utilisateur admin
```bash
docker-compose exec web python manage.py createsuperuser
```

### ✅ C'est prêt!

Accéder à:
- 🌐 Application: **http://10.105.42.118**
- 🔐 Admin: **http://10.105.42.118/admin/**
- 💚 Health: **http://10.105.42.118/health/**

---

## 📦 Infrastructure

| Service | Image | Port |
|---------|-------|------|
| Nginx | nginx:alpine | 80 |
| Django | custom (build) | 8000 |
| Redis | redis:7-alpine | 6379 |
| BD | SQLite (local) | - |

---

## 🔧 Configuration

Fichier `.env` contient:
- ✅ IP serveur: 10.105.42.118
- ✅ Domaine: LBVH.rezidor.com
- ✅ BD: SQLite (db.sqlite3)
- ✅ Cache: Redis
- ✅ Compression Gzip ON
- ✅ Optimisé mobiles

---

## 📱 Pour utilisateurs mobiles

Via WiFi HoistHospitality:
1. Ouvrir navigateur
2. Aller à: **10.105.42.118** ou **LBVH.rezidor.com**
3. Se connecter avec vos identifiants
4. Scanner les QR codes du matériel

**Optimisé pour:** Smartphones, connexion WiFi hôtel

---

## 🔍 Monitoring

```bash
# Voir l'état des services
docker-compose ps

# Logs en live
docker-compose logs -f web

# Vérifier la santé
curl http://10.105.42.118/health/
```

---

## 🛠️ Maintenance

```bash
# Redémarrer
docker-compose restart

# Arrêter (données persistées)
docker-compose down

# Sauvegarder BD
docker cp radgestmat_web:/app/db.sqlite3 ./backup/

# Logs complets
docker-compose logs web
```

---

## 📚 Documentation

- `DEPLOYMENT_GUIDE_PRODUCTION.md` - Guide détaillé
- `DEPLOYMENT_CONFIGURATION_SUMMARY.md` - Détails changements
- `DEPLOYMENT_CHECKLIST.md` - Checklist complète

---

## 🚨 Besoin d'aide?

1. Vérifier `.env` configuré
2. Consulter les logs: `docker-compose logs web`
3. Vérifier que port 80 est libre: `netstat -an | grep :80`
4. Relancer: `docker-compose restart`

---

**Status:** ✅ Prêt pour déploiement  
**Optimisations:** Mobiles + WiFi hôtel  
**Architecture:** Docker Compose (3 services)  
**BD:** SQLite local persisté

🎉 **Déployez et profitez!**
