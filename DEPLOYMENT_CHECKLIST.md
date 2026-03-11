# ✅ Checklist de Déploiement - RadGestMat

## 🎯 Avant le déploiement

- [ ] Serveur 10.105.42.118 accessible
- [ ] Docker et Docker Compose installés sur le serveur
- [ ] Port 80 libre (Nginx)
- [ ] Port 6379 libre (Redis)
- [ ] Port 8000 libre (Django/Gunicorn) - si test direct
- [ ] Répertoire `/opt/radgestmat/` créé
- [ ] Fichier `.env` présent et configuré
- [ ] Tous les fichiers du projet copiés sur serveur

## 🚀 Déploiement

### Option A: Script automatisé (Recommandé)

**Serveur Linux/WSL:**
```bash
cd /opt/radgestmat
chmod +x deploy.sh
./deploy.sh
```

- [ ] Script déploiement exécuté sans erreur
- [ ] Services Docker démarrés (vérifier: `docker-compose ps`)
- [ ] Image Django construite avec succès
- [ ] Migrations appliquées
- [ ] Static files collectés

**Serveur Windows (PowerShell):**
```powershell
cd C:\opt\radgestmat
.\deploy.ps1
```

- [ ] Script PowerShell exécuté
- [ ] Containers créés et en cours d'exécution
- [ ] Image Docker construite

### Option B: Déploiement manuel

```bash
cd /opt/radgestmat

# 1. Build image
docker-compose build

# 2. Démarrer services
docker-compose up -d

# 3. Appliquer migrations
docker-compose exec web python manage.py migrate

# 4. Collecter static files
docker-compose exec web python manage.py collectstatic --noinput

# 5. Créer superutilisateur
docker-compose exec web python manage.py createsuperuser
```

- [ ] Image construite
- [ ] Services démarrés
- [ ] Migrations appliquées
- [ ] Static files collectés
- [ ] Superutilisateur créé

## 🔍 Vérifications post-déploiement

### Services Docker

```bash
docker-compose ps
# Tous les containers doivent être "Up"
```

- [ ] `radgestmat_web` UP
- [ ] `radgestmat_nginx` UP
- [ ] `radgestmat_redis` UP

### Health checks

```bash
# Vérifier chaque service
docker-compose logs web    # Pas d'erreurs Django?
docker-compose logs nginx  # Nginx démarre?
docker-compose logs redis  # Redis actif?
```

- [ ] Pas d'erreurs critiques dans logs web
- [ ] Nginx démarre correctement
- [ ] Redis répond (PONG)

### Connectivité

```bash
# Sur le serveur
curl http://10.105.42.118/health/
# Doit retourner JSON avec "status": "healthy"

curl http://10.105.42.118/
# Doit retourner la page HTML de l'application

curl http://LBVH.rezidor.com/health/
# Doit fonctionner si DNS configuré
```

- [ ] Health endpoint répond (JSON)
- [ ] Application accessible via IP
- [ ] Application accessible via domaine (si DNS OK)
- [ ] Nginx répond correctement

### Base de données

```bash
docker-compose exec web python manage.py dbshell
# Doit ouvrir SQLite sans erreur
# Taper: .quit

# Ou vérifier le fichier SQLite existe
docker-compose exec web ls -lah db.sqlite3
```

- [ ] SQLite accessible
- [ ] Fichier db.sqlite3 créé
- [ ] Taille > 100 KB (après migrations)

### Cache Redis

```bash
docker-compose exec web redis-cli -h redis ping
# Doit retourner: PONG
```

- [ ] Redis répond au ping
- [ ] Connexion établie

### Accès administrateur

1. Ouvrir navigateur: http://10.105.42.118/admin/
2. Utiliser les identifiants superutilisateur créés
3. Vérifier authentification

- [ ] Page login affichée
- [ ] Authentification fonctionne
- [ ] Dashboard admin accessible
- [ ] Modèles visibles (Materiel, Client, etc.)

### Performance mobile

**Sur smartphone WiFi hôtel:**
1. Aller à: http://10.105.42.118
2. Charger la page
3. Ouvrir DevTools (F12)
4. Vérifier Network:
   - Temps chargement < 3s
   - Compression Gzip active
   - Cache utilisé

- [ ] Page charge rapidement sur mobile
- [ ] Gzip compression active (dans Headers)
- [ ] Static files en cache
- [ ] Images QR chargent vite

## 🛠️ Configurations optionnelles

### Email (notifications)

Si vous voulez activer l'email:

```bash
# Éditer .env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.votre-domaine.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre@email.com
EMAIL_HOST_PASSWORD=votre-password
```

- [ ] Variables email configurées (si nécessaire)
- [ ] Test email possible (depuis Django admin)

### WhatsApp (Twilio - optionnel)

```bash
# Dans .env
TWILIO_ACCOUNT_SID=votre_sid
TWILIO_AUTH_TOKEN=votre_token
```

- [ ] Twilio configuré (si souhaité)
- [ ] Test notification WhatsApp possible

## 📊 Monitoring continu

### Logs quotidiens

```bash
# Voir les 100 dernières lignes de logs
docker-compose logs --tail=100 web

# Voir les logs en temps réel
docker-compose logs -f web
```

- [ ] Logs consultables
- [ ] Pas d'erreurs critiques répétées
- [ ] Mémoriser les commandes pour monitoring

### Backup automatique

```bash
# Créer un script de backup quotidien
# Sauvegarder db.sqlite3

docker cp radgestmat_web:/app/db.sqlite3 /backup/db_$(date +%Y%m%d).sqlite3
```

- [ ] Répertoire backup créé
- [ ] Première sauvegarde effectuée
- [ ] Planifier backup quotidien (cron/task scheduler)

### Redémarrage après reboot serveur

```bash
# Docker compose devrait redémarrer automatiquement
# Grâce à: restart: unless-stopped

# Mais vérifier:
docker-compose ps
# Tous les containers doivent être Up après reboot
```

- [ ] Services redémarrent automatiquement après reboot

## 🚨 Troubleshooting

### Si une erreur survient

```bash
# 1. Voir les logs complets
docker-compose logs web
docker-compose logs nginx
docker-compose logs redis

# 2. Vérifier la configuration .env
cat .env
# Vérifier que ALLOWED_HOSTS contient votre IP/domaine

# 3. Redémarrer complètement
docker-compose down
docker-compose up -d
```

- [ ] Logs consultés en cas de problème
- [ ] Erreurs documentées
- [ ] .env revalidé si besoin

## ✨ Post-déploiement

### Créer contenu test

```bash
docker-compose exec web python manage.py shell
# Créer quelques Departements, Categorie, Materiel de test
```

- [ ] Données test créées
- [ ] Interface testée en tant que superutilisateur
- [ ] Création, lecture, mise à jour, suppression testées

### Notifier utilisateurs

- [ ] URL communiquée: http://10.105.42.118 ou LBVH.rezidor.com
- [ ] Guide utilisateur smartphone partagé
- [ ] Support disponible communiqué

### Documentation

- [ ] `DEPLOYMENT_GUIDE_PRODUCTION.md` accessible pour admin
- [ ] `DEPLOYMENT_CONFIGURATION_SUMMARY.md` conservé pour références
- [ ] Mots de passe/credentials sécurisés (pas dans git)

## 🎉 Déploiement réussi!

Une fois toutes les cases cochées ✅, vous êtes prêt!

**Récapitulatif:**
- ✅ Services Docker actifs
- ✅ Application accessible
- ✅ BD SQLite persistée
- ✅ Cache Redis fonctionnel
- ✅ Reverse proxy Nginx optimisé
- ✅ Accès mobiles WiFi configuré
- ✅ Admin Django fonctionnel
- ✅ Monitoring setup

---

**Date de déploiement:** _______________  
**Responsable:** _______________  
**Notes:** 

