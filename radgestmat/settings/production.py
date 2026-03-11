"""
Production settings for RadGestMat
Déploiement: 10.105.42.118 (LBVH.rezidor.com)
SQLite + Nginx + Redis
Optimisé pour accès mobiles via WiFi hôtelier
"""
import os
from pathlib import Path
from .base import *

# ====================
# SÉCURITÉ
# ====================
DEBUG = False

# Secret key from environment or generate
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')

# Server configuration
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ====================
# BASE DE DONNÉES - configurable via variables d'environnement (ex: Postgres)
# Reads DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT from environment
DATABASES = {
    'default': {
        'ENGINE': get_config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': get_config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
        'USER': get_config('DB_USER', default=''),
        'PASSWORD': get_config('DB_PASSWORD', default=''),
        'HOST': get_config('DB_HOST', default=''),
        'PORT': get_config('DB_PORT', default=''),
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '600')),
    }
}

# ====================
# SÉCURITÉ - HTTP sur réseau interne
# ====================
# Réseau interne d'hôtel sans HTTPS - pas de redirection SSL
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Headers de sécurité standard
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'

# CSRF trusted origins - IP et domaine du serveur
CSRF_TRUSTED_ORIGINS = [
    'http://10.105.42.118',
    'http://LBVH.rezidor.com',
    'http://localhost',
    'http://127.0.0.1',
]

# ====================
# EMAIL CONFIGURATION
# ====================
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'RadGestMat <noreply@LBVH.rezidor.com>')

# ====================
# SENTRY - Error tracking (optional)
# ====================
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
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

# ====================
# CACHE & SESSIONS - Redis
# ====================
# Redis pour cache et sessions (meilleur que BD pour performance)
try:
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/1')
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'TIMEOUT': 3600,  # 1 heure
        }
    }
    # Use cache for sessions (performant sur réseau WiFi)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
except Exception:
    # Fallback to database cache if Redis unavailable
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache_table',
        }
    }

# ====================
# OPTIMIZATION - Mobile & WiFi
# ====================
# Compression pour réduire bandwidth (important sur WiFi hôtelier)
MIDDLEWARE.insert(0, 'django.middleware.gzip.GZipMiddleware')

# Cache static files agressively
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# CDN URL pour QR codes
QR_DOMAIN = os.environ.get('QR_DOMAIN', 'http://LBVH.rezidor.com')
SITE_URL = os.environ.get('SITE_URL', QR_DOMAIN)

# ====================
# LOGGING
# ====================
LOGGING['root']['level'] = 'INFO'
LOGGING['loggers']['django']['level'] = 'INFO'
if 'file' in LOGGING['handlers']:
    LOGGING['handlers']['file']['formatter'] = 'json'

# ====================
# GUNICORN CONFIGURATION
# ====================
# These are used by docker-compose
GUNICORN_WORKERS = int(os.environ.get('GUNICORN_WORKERS', '3'))
GUNICORN_TIMEOUT = int(os.environ.get('GUNICORN_TIMEOUT', '120'))

