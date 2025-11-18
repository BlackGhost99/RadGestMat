# Guide de Déploiement RadGestMat - Production

## 📋 Table des Matières
1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Déploiement](#déploiement)
5. [Maintenance](#maintenance)
6. [Troubleshooting](#troubleshooting)

---

## Prérequis

### Serveur
- OS: Linux (Ubuntu 20.04+) ou Windows Server
- Python: 3.10+ (recommandé 3.14)
- Espace disque: 2GB minimum
- RAM: 2GB minimum
- Bande passante: 10Mbps minimum

### Logiciels
- Python 3.10+
- pip (Python package manager)
- PostgreSQL 12+ (recommandé pour production)
- Nginx ou Apache (reverse proxy)
- Supervisor ou systemd (process management)

### Accès
- Accès root/sudo au serveur
- Certificat SSL/TLS
- Domaine DNS configuré

---

## Installation

### 1. Préparation du serveur

```bash
# Mise à jour du système
sudo apt update
sudo apt upgrade -y

# Installation dépendances système
sudo apt install -y python3.10 python3-pip python3-venv
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y nginx
sudo apt install -y supervisor
sudo apt install -y git
```

### 2. Configuration PostgreSQL

```bash
# Créer utilisateur et base de données
sudo -u postgres psql << EOF
CREATE USER radgestmat WITH PASSWORD 'votre_mot_de_passe_secure';
ALTER ROLE radgestmat SET client_encoding TO 'utf8';
ALTER ROLE radgestmat SET default_transaction_isolation TO 'read committed';
ALTER ROLE radgestmat SET default_transaction_deferrable TO on;
ALTER ROLE radgestmat SET timezone TO 'UTC';
CREATE DATABASE radgestmat OWNER radgestmat;
GRANT ALL PRIVILEGES ON DATABASE radgestmat TO radgestmat;
EOF
```

### 3. Clonage et setup du projet

```bash
# Créer répertoire application
sudo mkdir -p /var/www/radgestmat
sudo chown $USER:$USER /var/www/radgestmat
cd /var/www/radgestmat

# Cloner le projet
git clone <votre_repo> .
# ou extraire l'archive
unzip radgestmat.zip

# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer dépendances Python
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Fichier requirements.txt

Créer `requirements.txt`:
```
Django==5.2.8
psycopg2-binary==2.9.9
python-decouple==3.8
qrcode==8.2
Pillow==12.0.0
gunicorn==21.2.0
whitenoise==6.6.0
```

Générer/vérifier:
```bash
pip freeze > requirements.txt
```

---

## Configuration

### 1. Variables d'environnement

Créer `.env` à la racine:
```
DEBUG=False
SECRET_KEY=votre_clé_secrète_très_sécurisée_min_50_chars
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
DATABASE_URL=postgresql://radgestmat:password@localhost:5432/radgestmat
STATIC_URL=/static/
STATIC_ROOT=/var/www/radgestmat/static/
MEDIA_URL=/media/
MEDIA_ROOT=/var/www/radgestmat/media/
```

### 2. Settings.py Production

```python
import os
from decouple import config

# Security
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'radgestmat',
        'USER': 'radgestmat',
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/radgestmat/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Middleware de sécurité
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... autres middlewares
]

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/www/radgestmat/logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

### 3. Migrations

```bash
# Appliquer migrations
python manage.py migrate --no-input

# Créer répertoires statiques
python manage.py collectstatic --no-input

# Créer superutilisateur
python manage.py createsuperuser
```

---

## Déploiement

### 1. Gunicorn

Créer `/etc/supervisor/conf.d/radgestmat.conf`:

```ini
[program:radgestmat]
directory=/var/www/radgestmat
command=/var/www/radgestmat/venv/bin/gunicorn \
  --workers 3 \
  --worker-class sync \
  --bind unix:/var/www/radgestmat/radgestmat.sock \
  --timeout 60 \
  --access-logfile /var/www/radgestmat/logs/access.log \
  --error-logfile /var/www/radgestmat/logs/error.log \
  radgestmat.wsgi:application

user=www-data
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=10
```

### 2. Nginx

Créer `/etc/nginx/sites-available/radgestmat`:

```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;
    
    # Rediriger HTTP vers HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com www.votre-domaine.com;
    
    # Certificats SSL
    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    
    # Sécurité SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Logging
    access_log /var/www/radgestmat/logs/nginx_access.log;
    error_log /var/www/radgestmat/logs/nginx_error.log;
    
    client_max_body_size 10M;
    
    # Static files
    location /static/ {
        alias /var/www/radgestmat/static/;
        expires 30d;
    }
    
    # Media files
    location /media/ {
        alias /var/www/radgestmat/media/;
        expires 7d;
    }
    
    # Proxy vers Gunicorn
    location / {
        proxy_pass http://unix:/var/www/radgestmat/radgestmat.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. SSL Let's Encrypt

```bash
# Installation certbot
sudo apt install -y certbot python3-certbot-nginx

# Générer certificat
sudo certbot certonly --standalone -d votre-domaine.com -d www.votre-domaine.com

# Renouvellement automatique
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### 4. Démarrage

```bash
# Activer Nginx
sudo ln -s /etc/nginx/sites-available/radgestmat /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Démarrer Supervisor
sudo systemctl start supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start radgestmat

# Vérifier
sudo supervisorctl status radgestmat
```

---

## Maintenance

### Sauvegardes

```bash
# Créer script de sauvegarde (cron)
#!/bin/bash
BACKUP_DIR="/var/backups/radgestmat"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup base de données
pg_dump -U radgestmat radgestmat | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup fichiers
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /var/www/radgestmat

# Cleanup (garder 7 jours)
find $BACKUP_DIR -type f -mtime +7 -delete

# Ajouter à crontab
0 2 * * * /path/to/backup.sh
```

### Monitoring

```bash
# CPU et mémoire
sudo systemctl status radgestmat
ps aux | grep gunicorn

# Logs
tail -f /var/www/radgestmat/logs/error.log
tail -f /var/www/radgestmat/logs/nginx_error.log

# Base de données
sudo -u postgres psql -d radgestmat -c "SELECT COUNT(*) FROM assets_materiel;"
```

### Mises à jour

```bash
# Arrêter l'application
sudo supervisorctl stop radgestmat

# Mettre à jour le code
cd /var/www/radgestmat
git pull origin main

# Installer dépendances
source venv/bin/activate
pip install -r requirements.txt

# Migrations
python manage.py migrate

# Collectstatic
python manage.py collectstatic --no-input

# Redémarrer
sudo supervisorctl start radgestmat
```

---

## Troubleshooting

### Problème: 502 Bad Gateway

**Causes:**
- Gunicorn pas démarré
- Socket permissions
- Erreur application

**Solutions:**
```bash
# Vérifier Gunicorn
sudo supervisorctl status radgestmat

# Voir les logs
sudo tail -50 /var/www/radgestmat/logs/error.log

# Redémarrer
sudo supervisorctl restart radgestmat
```

### Problème: Base de données connectée

**Solutions:**
```bash
# Vérifier PostgreSQL
sudo systemctl status postgresql

# Test connexion
psql -h localhost -U radgestmat -d radgestmat

# Vérifier permissions
sudo -u postgres psql -d radgestmat -c "\du"
```

### Problème: Fichiers statiques non chargés

**Solutions:**
```bash
# Recollectstatic
python manage.py collectstatic --clear --no-input

# Vérifier permissions
sudo chown -R www-data:www-data /var/www/radgestmat/static/
sudo chmod -R 755 /var/www/radgestmat/static/

# Redémarrer Nginx
sudo systemctl restart nginx
```

### Problème: Mémoire insuffisante

**Solutions:**
```bash
# Augmenter workers Gunicorn (réduire si mémoire limitée)
# Modifier gunicorn command:
--workers 2  # au lieu de 3

# Ajouter swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Checklist de Production

- [ ] Certificat SSL installé
- [ ] DEBUG = False dans settings
- [ ] SECRET_KEY changé
- [ ] ALLOWED_HOSTS configuré
- [ ] BASE DE DONNÉES PostgreSQL
- [ ] Sauvegardes automatisées
- [ ] Logs configurés
- [ ] Monitoring en place
- [ ] HTTPS redirigé
- [ ] Permissions fichiers OK
- [ ] Tests de charge effectués
- [ ] Documentation utilisateur ready

---

## Support

**En cas de problème:**
1. Vérifier les logs: `/var/www/radgestmat/logs/`
2. Consulter documentation Django
3. Contacter l'équipe de support

---

**Dernière mise à jour:** Novembre 2024
**Version:** 1.0.0 Production
