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
SECRET_KEY = os.environ['SECRET_KEY']

# Server configuration
ALLOWED_HOSTS = [host.strip() for host in os.environ.get('ALLOWED_HOSTS', os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')).split(',') if host.strip()]

# ====================
# BASE DE DONNÉES - Render / Supabase PostgreSQL
# DATABASE_URL is required for hosted production to prevent accidental SQLite use.
import dj_database_url

if not os.environ.get('DATABASE_URL'):
    raise RuntimeError('DATABASE_URL must be configured for production')

DATABASES = {
    'default': dj_database_url.config(
        env='DATABASE_URL',
        conn_max_age=0,  # Session pooler: do not retain Django connections
        ssl_require=True,
    )
}

# ====================
# SÉCURITÉ - HTTPS sur Render
# Render terminates HTTPS at its reverse proxy.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'

# Set ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS for the actual Render domain.
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]
if not CSRF_TRUSTED_ORIGINS and os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    CSRF_TRUSTED_ORIGINS = ['https://' + os.environ['RENDER_EXTERNAL_HOSTNAME']]

# ====================
# EMAIL CONFIGURATION
# ====================
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_DELIVERY_METHOD = os.environ.get('EMAIL_DELIVERY_METHOD', 'smtp')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.office365.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in {'1', 'true', 'yes', 'on'}
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_TIMEOUT = int(os.environ.get('EMAIL_TIMEOUT', '30'))
DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    'RadGestMat <helpdesk.libreville@radissonblu.com>',
)
MICROSOFT_TENANT_ID = os.environ.get('MICROSOFT_TENANT_ID', '')
MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID', '')
MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET', '')
MICROSOFT_GRAPH_SENDER = os.environ.get('MICROSOFT_GRAPH_SENDER', '')
MICROSOFT_GRAPH_SAVE_TO_SENT_ITEMS = (
    os.environ.get('MICROSOFT_GRAPH_SAVE_TO_SENT_ITEMS', 'True').lower()
    in {'1', 'true', 'yes', 'on'}
)

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
# CACHE & SESSIONS - database-backed sessions work without Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'radgestmat-render-cache',
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ====================
# OPTIMIZATION - Mobile & WiFi
# ====================
# Compression pour réduire bandwidth (important sur WiFi hôtelier)
MIDDLEWARE.insert(0, 'django.middleware.gzip.GZipMiddleware')

# Serve CSS/JS with WhiteNoise (no Redis or Nginx required)
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,
                      'whitenoise.middleware.WhiteNoiseMiddleware')
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# QR Code domain configuration
QR_DOMAIN = os.environ.get('QR_DOMAIN', os.environ.get('SITE_URL', ''))
SITE_URL = os.environ.get('SITE_URL', QR_DOMAIN)

# ====================
# LOGGING - Render captures stdout/stderr; no log files needed.
LOGGING['handlers'] = {
    'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'verbose',
    },
}
LOGGING['root']['handlers'] = ['console']
LOGGING['root']['level'] = 'INFO'
for logger in LOGGING['loggers'].values():
    logger['handlers'] = ['console']

# ====================
# GUNICORN CONFIGURATION
# ====================
# These are used by docker-compose
GUNICORN_WORKERS = int(os.environ.get('GUNICORN_WORKERS', '3'))
GUNICORN_TIMEOUT = int(os.environ.get('GUNICORN_TIMEOUT', '120'))

