"""
Local network settings for RadGestMat
Hébergement sur PC Windows dans réseau admin (domaine)
Détection automatique de l'IP locale pour ALLOWED_HOSTS
"""
import os
import socket
from pathlib import Path
from .production import *

# ====================
# DÉTECTION IP LOCALE AUTOMATIQUE
# ====================
def get_local_ip():
    """
    Détecte l'IP locale du réseau admin.
    Essaie plusieurs méthodes pour trouver l'IP IPv4 active.
    """
    # Méthode 1: Variable d'environnement (définie par script PowerShell)
    local_ip = os.environ.get('LOCAL_NETWORK_IP')
    if local_ip:
        return local_ip.strip()
    
    # Méthode 2: Connexion socket pour obtenir IP active
    try:
        # Se connecter à une adresse externe pour déterminer l'interface active
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Ne se connecte pas réellement, juste pour déterminer l'interface
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and ip != '127.0.0.1':
            return ip
    except Exception:
        pass
    
    # Méthode 3: Nom d'hôte réseau
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip and ip != '127.0.0.1':
            return ip
    except Exception:
        pass
    
    # Fallback: localhost
    return '127.0.0.1'

# Obtenir l'IP locale
LOCAL_IP = get_local_ip()

# ====================
# CONFIGURATION SERVEUR
# ====================
# ALLOWED_HOSTS inclut l'IP locale détectée + localhost
# Permet aussi les adresses du réseau local (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
allowed_hosts_list = [
    LOCAL_IP,
    'localhost',
    '127.0.0.1',
    '0.0.0.0',  # Pour bind sur toutes les interfaces
]

# Ajouter l'IP depuis variable d'environnement si fournie
env_allowed = os.environ.get('ALLOWED_HOSTS', '')
if env_allowed:
    allowed_hosts_list.extend([h.strip() for h in env_allowed.split(',') if h.strip()])

# Supprimer les doublons
ALLOWED_HOSTS = list(dict.fromkeys(allowed_hosts_list))

# ====================
# CSRF TRUSTED ORIGINS
# ====================
# Ajouter l'IP locale aux origines CSRF autorisées
csrf_origins = [
    f'http://{LOCAL_IP}',
    f'http://{LOCAL_IP}:8000',
    'http://localhost',
    'http://localhost:8000',
    'http://127.0.0.1',
    'http://127.0.0.1:8000',
]

# Ajouter depuis variable d'environnement si fournie
env_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if env_csrf:
    csrf_origins.extend([o.strip() for o in env_csrf.split(',') if o.strip()])

CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(csrf_origins))

# ====================
# BASE DE DONNÉES
# ====================
# Utiliser SQLite par défaut pour simplicité (pas de Redis requis)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Override si variables d'environnement spécifiées
if os.environ.get('DB_ENGINE'):
    DATABASES['default'] = {
        'ENGINE': get_config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': get_config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
        'USER': get_config('DB_USER', default=''),
        'PASSWORD': get_config('DB_PASSWORD', default=''),
        'HOST': get_config('DB_HOST', default=''),
        'PORT': get_config('DB_PORT', default=''),
    }

# ====================
# CACHE - Local Memory (pas Redis requis)
# ====================
# Cache en mémoire locale (suffisant pour petit réseau)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'radgestmat-local-cache',
    }
}

# Sessions en base de données (plus simple que cache pour réseau local)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ====================
# QR CODE DOMAIN
# ====================
# Utiliser l'IP locale pour les QR codes
QR_DOMAIN = os.environ.get('QR_DOMAIN', f'http://{LOCAL_IP}:8000')

# ====================
# LOGGING
# ====================
# Logging plus verbeux pour réseau local (débug plus facile)
LOGGING['root']['level'] = 'INFO'
LOGGING['loggers']['django']['level'] = 'INFO'

# Ajouter l'IP dans les logs
LOGGING['formatters']['verbose']['format'] = (
    '{levelname} {asctime} {module} {process:d} {thread:d} '
    f'[IP:{LOCAL_IP}] {{message}}'
)

# ====================
# DEBUG MODE
# ====================
# Peut être activé pour réseau local (plus facile de débugger)
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# ====================
# INFORMATION IP
# ====================
# Stocker l'IP détectée pour affichage dans les logs
print(f"[RadGestMat] Configuration réseau local - IP détectée: {LOCAL_IP}")
print(f"[RadGestMat] ALLOWED_HOSTS: {', '.join(ALLOWED_HOSTS)}")
