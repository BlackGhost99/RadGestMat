"""
Production settings for RadGestMat
Déploiement sur serveur local d'entreprise (LAN)
"""
import os
from pathlib import Path
from .base import *

# ====================
# SÉCURITÉ
# ====================
DEBUG = False

# IMPORTANT : Générer avec : python -c "import secrets; print(secrets.token_urlsafe(50))"
SECRET_KEY = os.environ.get('SECRET_KEY', BASE_DIR.parent / '.secret_key')
if isinstance(SECRET_KEY, Path):
    if SECRET_KEY.exists():
        SECRET_KEY = SECRET_KEY.read_text().strip()
    else:
        import secrets
        key = secrets.token_urlsafe(50)
        SECRET_KEY.write_text(key)
        SECRET_KEY = key

# Ajouter l'IP de votre serveur (ex: 192.168.1.100)
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ====================
# BASE DE DONNÉES
# ====================

# Option 1 : PostgreSQL (Recommandé)
if os.environ.get('USE_POSTGRESQL', 'false').lower() == 'true':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'radgestmat'),
            'USER': os.environ.get('DB_USER', 'radgestmat_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'changeme'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CONN_MAX_AGE': 600,
        }
    }
else:
    # Option 2 : SQLite (OK pour < 50 utilisateurs)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ====================
# SÉCURITÉ HTTPS (Désactivé pour réseau interne HTTP)
# ====================
SECURE_SSL_REDIRECT = False  # Mettre True si HTTPS configuré
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False  # Mettre True si HTTPS
CSRF_COOKIE_SECURE = False  # Mettre True si HTTPS

# Headers de sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'

# CSRF (Ajouter l'IP du serveur)
CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    # Ajouter : 'http://192.168.1.100'
]

# ====================
# EMAIL CONFIGURATION
# ====================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'RadGestMat <noreply@radgestmat.local>'

if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
    except ImportError:
        pass
    else:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
            environment='production',
        )

# CORS - Restricted in production (uncomment when corsheaders is installed)
# CORS_ALLOW_ALL_ORIGINS = False

# Cache - Redis recommended for production
try:
    from decouple import config
    REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/1')
except ImportError:
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}

# Logging - Less verbose, more structured in production
LOGGING['root']['level'] = 'INFO'
LOGGING['handlers']['file']['formatter'] = 'json'

