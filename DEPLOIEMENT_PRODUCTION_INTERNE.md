# 🏢 Guide de Déploiement Production Interne

## 📋 Vue d'Ensemble

**Type** : Déploiement sur serveur local Windows/Linux  
**Accès** : Réseau local entreprise (LAN + WiFi)  
**Coût** : 0€ (pas d'hébergement cloud)  
**Clients** : PC + Smartphones sur le même réseau

---

## 🖥️ Option 1 : Serveur Windows (Recommandé pour entreprise Windows)

### **Prérequis**

- Windows Server 2016+ ou Windows 10/11 Pro
- Python 3.11+
- Accès administrateur
- IP fixe sur le réseau local

### **1. Installation des Dépendances**

```powershell
# Installer Python 3.11 depuis python.org
# Vérifier l'installation
python --version

# Installer les packages système
pip install --upgrade pip setuptools wheel
```

### **2. Configuration de la Base de Données**

#### **Option A : PostgreSQL (Recommandé pour production)**

```powershell
# Télécharger PostgreSQL : https://www.postgresql.org/download/windows/
# Installer et configurer

# Créer la base de données
psql -U postgres
CREATE DATABASE radgestmat;
CREATE USER radgestmat_user WITH PASSWORD 'VotreMotDePasseSecurise123!';
GRANT ALL PRIVILEGES ON DATABASE radgestmat TO radgestmat_user;
\q
```

Modifier `radgestmat/settings/production.py` :

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'radgestmat',
        'USER': 'radgestmat_user',
        'PASSWORD': 'VotreMotDePasseSecurise123!',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

#### **Option B : SQLite (Simple, OK pour petite entreprise)**

SQLite déjà configuré dans `settings/development.py`. Aucun changement nécessaire.

### **3. Configuration du Projet**

```powershell
# Aller dans le dossier du projet
cd C:\RadGestMat\RadGestMat

# Créer l'environnement virtuel
python -m venv env_prod
.\env_prod\Scripts\Activate.ps1

# Installer les dépendances
pip install -r requirements.txt
pip install gunicorn psycopg2-binary  # Si PostgreSQL

# Variables d'environnement (créer .env.production)
$env:DJANGO_SETTINGS_MODULE = "radgestmat.settings.production"
$env:SECRET_KEY = "votre-cle-secrete-super-longue-et-aleatoire-123456789"
$env:ALLOWED_HOSTS = "192.168.1.100,localhost,127.0.0.1"  # IP du serveur

# Migrations et fichiers statiques
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### **4. Créer le Service Windows**

**Installer NSSM (Non-Sucking Service Manager)** :

```powershell
# Télécharger NSSM : https://nssm.cc/download
# Extraire dans C:\nssm

# Créer le service Django
C:\nssm\nssm.exe install RadGestMat "C:\RadGestMat\RadGestMat\env_prod\Scripts\python.exe"
C:\nssm\nssm.exe set RadGestMat AppParameters "manage.py runserver 0.0.0.0:8000"
C:\nssm\nssm.exe set RadGestMat AppDirectory "C:\RadGestMat\RadGestMat"
C:\nssm\nssm.exe set RadGestMat DisplayName "RadGestMat - Gestion Matériel"
C:\nssm\nssm.exe set RadGestMat Description "Système de gestion de matériel RadGestMat"
C:\nssm\nssm.exe set RadGestMat Start SERVICE_AUTO_START

# Démarrer le service
C:\nssm\nssm.exe start RadGestMat

# Vérifier le statut
C:\nssm\nssm.exe status RadGestMat
```

### **5. Configuration du Pare-feu**

```powershell
# Autoriser le port 8000
New-NetFirewallRule -DisplayName "RadGestMat Django" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

### **6. Trouver l'IP du Serveur**

```powershell
ipconfig

# Chercher "IPv4 Address" : exemple 192.168.1.100
# Configurer une IP fixe dans les paramètres réseau Windows
```

---

## 🐧 Option 2 : Serveur Linux (Ubuntu/Debian)

### **1. Installation**

```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installer Python et dépendances
sudo apt install python3.11 python3.11-venv python3-pip postgresql nginx -y

# Créer utilisateur système
sudo useradd -m -s /bin/bash radgestmat
sudo su - radgestmat

# Cloner ou copier le projet
cd /home/radgestmat
# Copier vos fichiers ici

# Créer environnement virtuel
python3.11 -m venv env_prod
source env_prod/bin/activate

# Installer dépendances
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### **2. Configuration PostgreSQL**

```bash
sudo -u postgres psql
CREATE DATABASE radgestmat;
CREATE USER radgestmat_user WITH PASSWORD 'MotDePasseSecurise123!';
GRANT ALL PRIVILEGES ON DATABASE radgestmat TO radgestmat_user;
\q
```

### **3. Configuration Gunicorn**

Créer `/home/radgestmat/gunicorn_config.py` :

```python
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
timeout = 120
accesslog = "/home/radgestmat/logs/gunicorn_access.log"
errorlog = "/home/radgestmat/logs/gunicorn_error.log"
loglevel = "info"
```

### **4. Systemd Service**

Créer `/etc/systemd/system/radgestmat.service` :

```ini
[Unit]
Description=RadGestMat Django Application
After=network.target

[Service]
Type=notify
User=radgestmat
Group=radgestmat
WorkingDirectory=/home/radgestmat/RadGestMat
Environment="DJANGO_SETTINGS_MODULE=radgestmat.settings.production"
Environment="SECRET_KEY=votre-cle-secrete-super-longue"
ExecStart=/home/radgestmat/env_prod/bin/gunicorn radgestmat.wsgi:application -c /home/radgestmat/gunicorn_config.py
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Activer et démarrer :

```bash
sudo systemctl daemon-reload
sudo systemctl enable radgestmat
sudo systemctl start radgestmat
sudo systemctl status radgestmat
```

### **5. Configuration Nginx**

Créer `/etc/nginx/sites-available/radgestmat` :

```nginx
server {
    listen 80;
    server_name 192.168.1.100;  # IP du serveur

    client_max_body_size 100M;

    location /static/ {
        alias /home/radgestmat/RadGestMat/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/radgestmat/RadGestMat/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

Activer la configuration :

```bash
sudo ln -s /etc/nginx/sites-available/radgestmat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### **6. Pare-feu**

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 📱 Accès depuis PC et Smartphone

### **Sur PC (même réseau)**

1. Ouvrir le navigateur
2. Aller sur `http://192.168.1.100` (remplacer par l'IP du serveur)
3. Se connecter avec le compte superuser

### **Sur Smartphone (WiFi entreprise)**

1. Connecter le smartphone au WiFi de l'entreprise
2. Ouvrir Chrome/Safari
3. Aller sur `http://192.168.1.100`
4. Ajouter à l'écran d'accueil pour un accès rapide

**Astuce PWA** : Le site peut fonctionner comme une application native !

---

## 🔒 Sécurité Production

### **1. Modifier `settings/production.py`**

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SÉCURITÉ
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'changez-moi-en-production!')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

# CSRF
CSRF_COOKIE_SECURE = False  # True si HTTPS
SESSION_COOKIE_SECURE = False  # True si HTTPS
SECURE_SSL_REDIRECT = False  # True si HTTPS

# Headers de sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CORS (si API utilisée)
CORS_ALLOWED_ORIGINS = [
    "http://192.168.1.100",
    "http://localhost",
]

# Logging production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/radgestmat.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### **2. Variables d'Environnement**

Créer `.env.production` :

```env
DJANGO_SETTINGS_MODULE=radgestmat.settings.production
SECRET_KEY=generer-une-cle-avec-python-secrets-token_urlsafe50
ALLOWED_HOSTS=192.168.1.100,localhost,127.0.0.1
DATABASE_URL=postgresql://radgestmat_user:password@localhost:5432/radgestmat

# Email (Gmail ou SMTP entreprise)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre.email@entreprise.com
EMAIL_HOST_PASSWORD=mot_de_passe_application

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=votre_sid
TWILIO_AUTH_TOKEN=votre_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

---

## 🔄 APScheduler en Production

### **Windows**

Le service NSSM lancera automatiquement le scheduler via `manage.py runserver`.

Pour un scheduler séparé :

```powershell
C:\nssm\nssm.exe install RadGestMatScheduler "C:\RadGestMat\RadGestMat\env_prod\Scripts\python.exe"
C:\nssm\nssm.exe set RadGestMatScheduler AppParameters "manage.py run_scheduler"
C:\nssm\nssm.exe set RadGestMatScheduler AppDirectory "C:\RadGestMat\RadGestMat"
C:\nssm\nssm.exe start RadGestMatScheduler
```

### **Linux**

Créer `/etc/systemd/system/radgestmat-scheduler.service` :

```ini
[Unit]
Description=RadGestMat APScheduler
After=network.target

[Service]
Type=simple
User=radgestmat
WorkingDirectory=/home/radgestmat/RadGestMat
Environment="DJANGO_SETTINGS_MODULE=radgestmat.settings.production"
ExecStart=/home/radgestmat/env_prod/bin/python manage.py run_scheduler
Restart=always

[Install]
WantedBy=multi-user.target
```

Activer :

```bash
sudo systemctl enable radgestmat-scheduler
sudo systemctl start radgestmat-scheduler
```

---

## 📊 Monitoring et Maintenance

### **Logs**

**Windows** :
```powershell
# Logs du service
Get-EventLog -LogName Application -Source RadGestMat -Newest 50

# Logs Django
Get-Content C:\RadGestMat\RadGestMat\logs\radgestmat.log -Tail 100 -Wait
```

**Linux** :
```bash
# Logs Systemd
sudo journalctl -u radgestmat -f

# Logs Django
tail -f /home/radgestmat/logs/radgestmat.log
```

### **Sauvegardes Automatiques**

**Script PowerShell** (`scripts/backup_prod.ps1`) :

```powershell
$BackupDir = "C:\RadGestMat\backups"
$Date = Get-Date -Format "yyyyMMdd_HHmm"

# Backup SQLite
Copy-Item "C:\RadGestMat\RadGestMat\db.sqlite3" "$BackupDir\db_$Date.sqlite3"

# Backup PostgreSQL
& "C:\Program Files\PostgreSQL\15\bin\pg_dump.exe" -U radgestmat_user -d radgestmat -f "$BackupDir\db_$Date.sql"

# Cleanup old backups (garder 7 jours)
Get-ChildItem $BackupDir -Filter "db_*.sqlite3" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item
```

Tâche planifiée Windows :
```powershell
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "C:\RadGestMat\RadGestMat\scripts\backup_prod.ps1"
$Trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"
Register-ScheduledTask -TaskName "RadGestMat Backup" -Action $Action -Trigger $Trigger
```

---

## 🌐 Accès Externe (Optionnel)

Si vous voulez accéder depuis l'extérieur de l'entreprise :

### **Option 1 : VPN**

Utiliser le VPN de l'entreprise pour se connecter au réseau local.

### **Option 2 : Redirection de Port (Router)**

1. Configurer le routeur pour rediriger le port 80 externe vers `192.168.1.100:80`
2. Utiliser un service DNS dynamique (No-IP, DuckDNS) gratuit
3. **Attention** : Nécessite HTTPS obligatoire (Let's Encrypt gratuit)

---

## ✅ Checklist de Déploiement

### **Avant Mise en Production**

- [ ] PostgreSQL installé et configuré
- [ ] SECRET_KEY générée (50+ caractères aléatoires)
- [ ] DEBUG=False dans settings/production.py
- [ ] ALLOWED_HOSTS configuré avec l'IP du serveur
- [ ] Migrations appliquées : `python manage.py migrate`
- [ ] Fichiers statiques collectés : `python manage.py collectstatic`
- [ ] Superuser créé : `python manage.py createsuperuser`
- [ ] Service Windows/Linux configuré et démarré
- [ ] Pare-feu configuré (port 80/443/8000)
- [ ] Backup automatique configuré
- [ ] IP fixe configurée sur le serveur
- [ ] Tests d'accès depuis PC et smartphone
- [ ] Email SMTP configuré
- [ ] Twilio WhatsApp configuré (optionnel)
- [ ] APScheduler démarré
- [ ] Logs vérifiés

### **Tests de Validation**

```bash
# Accès web
curl http://192.168.1.100

# Statut du service (Linux)
sudo systemctl status radgestmat

# Logs en temps réel
tail -f /home/radgestmat/logs/radgestmat.log

# Test email
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Message test', 'from@test.com', ['to@test.com'])

# Test WhatsApp
python scripts/test_whatsapp_direct.py
```

---

## 🆘 Dépannage

### **Erreur : Can't connect to server**

```bash
# Vérifier le service
sudo systemctl status radgestmat

# Vérifier les logs
sudo journalctl -u radgestmat -n 50

# Vérifier les ports
sudo netstat -tulpn | grep :8000
```

### **Erreur : 502 Bad Gateway (Nginx)**

```bash
# Vérifier Gunicorn
ps aux | grep gunicorn

# Redémarrer les services
sudo systemctl restart radgestmat
sudo systemctl restart nginx
```

### **Accès depuis smartphone impossible**

1. Vérifier que le smartphone est sur le même WiFi
2. Désactiver temporairement le pare-feu pour tester
3. Vérifier l'IP du serveur : `ipconfig` (Windows) ou `ip addr` (Linux)

---

## 📞 Support

Pour toute question, vérifier :
- Logs : `logs/radgestmat.log`
- Documentation complète : `NOTIFICATIONS_COMPLETE.md`
- Tests : `scripts/test_notifications_complete.py`

**Bonne mise en production ! 🚀**
