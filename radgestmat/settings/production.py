"""
Production settings for RadGestMat
"""
import os
from .base import *

DEBUG = False

# Security settings for production
try:
    from decouple import config
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
except ImportError:
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database - PostgreSQL recommended for production
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Static files - Use WhiteNoise or CDN in production
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Email - SMTP in production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Sentry error tracking (if configured)
try:
    from decouple import config
    SENTRY_DSN = config('SENTRY_DSN', default='')
except ImportError:
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

