"""
Development settings for RadGestMat
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database - SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug toolbar (if installed)
try:
    from decouple import config
    USE_DEBUG_TOOLBAR = config('USE_DEBUG_TOOLBAR', default=False, cast=bool)
except ImportError:
    USE_DEBUG_TOOLBAR = os.environ.get('USE_DEBUG_TOOLBAR', 'False').lower() == 'true'

if USE_DEBUG_TOOLBAR:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']

# CORS - Allow all in development (uncomment when corsheaders is installed)
# CORS_ALLOW_ALL_ORIGINS = True

# Security settings relaxed for development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Logging - More verbose in development
LOGGING['root']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'

