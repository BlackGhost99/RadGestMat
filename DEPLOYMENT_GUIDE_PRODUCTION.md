# Guide de Déploiement - RadGestMat sur 10.105.42.118

## 📋 Configuration pour votre serveur

**Serveur**: 10.105.42.118 (LBVH.rezidor.com)  
**BD**: SQLite (local, simple, performant)  
**Cache**: Redis 7  
**Reverse Proxy**: Nginx  
**App Server**: Gunicorn + Django 5.2.8  
**Utilisateurs cibles**: Smartphones (WiFi Hoisthospitality)

---

## 🚀 Étapes de déploiement

### 1. Préparation du serveur

```powershell
# Sur le serveur 10.105.42.118

# Vérifier Docker et Docker Compose
docker --version
docker-compose --version

# Créer répertoire de déploiement
mkdir -p /opt/radgestmat
cd /opt/radgestmat
```

### 2. Copier les fichiers du projet

```powershell
# Copier depuis votre développement vers le serveur
# Option 1: Via SCP/WinSCP
scp -r RadGestMat/* user@10.105.42.118:/opt/radgestmat/

# Option 2: Via Git
cd /opt/radgestmat
git clone https://github.com/BlackGhost99/RadGestMat.git .
```

### 3. Configurer les variables d'environnement

Le fichier `.env` est déjà créé à la racine avec les bons paramètres :

```bash
# Fichier: .env (à la racine du projet)
# Vérifier ces valeurs critiques:

DEBUG=False
DJANGO_SETTINGS_MODULE=radgestmat.settings.production
ALLOWED_HOSTS=10.105.42.118,LBVH.rezidor.com,localhost,127.0.0.1

# Génération SECRET_KEY (si besoin de changer):
# python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 4. Démarrer les services Docker

```bash
cd /opt/radgestmat

# Construire l'image Docker
docker-compose build

# Démarrer tous les services (redis, django, nginx)
docker-compose up -d

# Vérifier l'état des services
docker-compose ps
docker-compose logs -f web
```

### 5. Initialiser la base de données

```bash
# Les migrations se lancent automatiquement au démarrage
# Mais vous pouvez les forcer:

docker-compose exec web python manage.py migrate

# Créer un superutilisateur
docker-compose exec web python manage.py createsuperuser
# Entrer les identifiants (email, password)

# Créer des données de test (optionnel)
docker-compose exec web python create_test_data.py

# Collecter les fichiers statiques
docker-compose exec web python manage.py collectstatic --noinput
```

---

## 🌐 Accès à l'application

### URLs disponibles

| Service | URL | Port |
|---------|-----|------|
| Application | http://10.105.42.118 | 80 |
| Application | http://LBVH.rezidor.com | 80 |
| Admin Django | http://10.105.42.118/admin/ | 80 |
| Redis | localhost:6379 | 6379 |

### Test de santé

```bash
# Vérifier que les services répondent
curl http://10.105.42.118/health/
curl http://LBVH.rezidor.com/health/

# Logs en temps réel
docker-compose logs -f web nginx redis
```

---

## 📱 Optimisations pour accès mobiles

✅ **Compression Gzip** - Réduction 60-70% du trafic  
✅ **Cache agressif** - Static files mis en cache 30 jours  
✅ **Sessions Redis** - Plus rapide que la BD  
✅ **Buffers Nginx** - Optimisé pour connexions WiFi lentes  
✅ **Timeouts adaptés** - 60s pour mobiles  
✅ **Minification** - CSS et JS compressés

---

## 🔧 Maintenance et monitoring

### Logs

```bash
# Logs en live (web application)
docker-compose logs -f web

# Logs Nginx
docker-compose logs -f nginx

# Logs Redis
docker-compose logs -f redis

# Logs avec timestamps
docker-compose logs --timestamps web
```

### Sauvegardes

```bash
# Sauvegarder la base SQLite
docker-compose exec web cp db.sqlite3 /app/backups/db_$(date +%Y%m%d_%H%M%S).sqlite3

# Ou depuis l'hôte
docker cp radgestmat_web:/app/db.sqlite3 ./backups/db_backup_$(date +%Y%m%d).sqlite3
```

### Redémarrage

```bash
# Redémarrer tous les services
docker-compose restart

# Redémarrer un service spécifique
docker-compose restart web
docker-compose restart nginx
docker-compose restart redis
```

### Arrêt complet

```bash
# Arrêter les services (data persistée)
docker-compose down

# Arrêter et supprimer les volumes (attention!)
docker-compose down -v
```

---

## 🐛 Troubleshooting

### Port 80 déjà utilisé

```bash
# Identifier le processus
netstat -ano | findstr :80

# Ou avec Nginx spécifique
docker-compose down
docker ps  # Vérifier qu'aucun container reste
```

### Cache Redis non accessible

```bash
# Vérifier connexion Redis
docker-compose exec web redis-cli -h redis ping
# Doit retourner: PONG
```

### BD SQLite verrouillée

```bash
# SQLite peut être verrouillé par plusieurs processus
# Solution: Réduire le nombre de workers
# Dans .env: GUNICORN_WORKERS=2
docker-compose down
docker-compose up -d
```

### Permissions fichiers

```bash
# Si problème d'accès aux fichiers
docker-compose exec web chmod -R 755 /app/db.sqlite3
docker-compose exec web chown -R appuser:appuser /app/media /app/logs
```

### WebSocket (si utilisé plus tard)

```bash
# Configuration pour WebSockets (Daphne)
# À ajouter dans docker-compose.yml si nécessaire
# Actuellement: Gunicorn synchrone suffit
```

---

## 📊 Performance & Ressources

### Consommation typique

- **CPU**: 10-20% (3 workers Gunicorn)
- **RAM**: 300-400 MB
- **Disque**: 500 MB (DB + static files)
- **Network**: ~2-5 Mbps (selon charge)

### Scaling (si besoin)

```bash
# Augmenter workers Gunicorn
# Dans .env: GUNICORN_WORKERS=5

# Optimiser timeout pour mobiles
# Dans .env: GUNICORN_TIMEOUT=120

# Redémarrer
docker-compose down && docker-compose up -d
```

---

## 🔐 Sécurité

✅ User non-root dans Docker  
✅ SECRET_KEY généré de manière sécurisée  
✅ Debug=False en production  
✅ Headers de sécurité (X-Frame-Options, X-Content-Type-Options)  
✅ CSRF protection activée  
✅ SQLite local (données hôtel protégées)  
✅ Connexion HTTP sur réseau interne (pas HTTPS requis)

---

## 📝 Configuration avancée

### Email (notifications)

```bash
# Dans .env, configurer:
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=votre-smtp.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre-email
EMAIL_HOST_PASSWORD=votre-password
```

### WhatsApp Twilio (optionnel)

```bash
# Si vous voulez les notifications WhatsApp:
TWILIO_ACCOUNT_SID=votre_sid
TWILIO_AUTH_TOKEN=votre_token
```

### Monitoring avec Sentry (optionnel)

```bash
# Pour error tracking en prod:
SENTRY_DSN=https://votre-sentry-dsn
```

---

## 📞 Support

Pour toute question, consultez:
- `/docs/` - Documentation complète du projet
- `README.md` - Documentation générale
- Logs Docker - `docker-compose logs web`

---

**Déployé sur**: 10.105.42.118 (LBVH.rezidor.com)  
**Date**: Décembre 2025  
**Optimisé pour**: Accès mobiles WiFi hôtelier
