"""
Base settings for RadGestMat
Common settings shared across all environments
"""
import os
from pathlib import Path

# Try to use decouple, fallback to os.environ if not available
try:
    from decouple import config, Csv
    def get_config(key, default=None, cast=None):
        if cast is None:
            return config(key, default=default)
        return config(key, default=default, cast=cast)
    def get_csv(key, default=''):
        return config(key, default=default, cast=Csv())
except ImportError:
    # Fallback if decouple is not installed
    def get_config(key, default=None, cast=None):
        value = os.environ.get(key, default)
        if cast and value:
            return cast(value)
        return value
    def get_csv(key, default=''):
        value = os.environ.get(key, default)
        if value:
            return [v.strip() for v in value.split(',') if v.strip()]
        return []

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security Settings
SECRET_KEY = get_config('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = get_config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = get_csv('ALLOWED_HOSTS', default='localhost,127.0.0.1')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps (optional)
    # 'rest_framework',  # Uncomment when installed
    # 'corsheaders',  # Uncomment when installed
    # Local apps
    'users',
    'assets',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 'corsheaders.middleware.CorsMiddleware',  # Uncomment when corsheaders is installed
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom middleware
    'users.middleware.DepartementMiddleware',
]

ROOT_URLCONF = 'radgestmat.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'users.context_processors.user_profile',
                'assets.context_processors.alertes_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'radgestmat.wsgi.application'
ASGI_APPLICATION = 'radgestmat.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': get_config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': get_config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
        'USER': get_config('DB_USER', default=''),
        'PASSWORD': get_config('DB_PASSWORD', default=''),
        'HOST': get_config('DB_HOST', default=''),
        'PORT': get_config('DB_PORT', default=''),
        'OPTIONS': {
            'charset': 'utf8mb4',
        } if get_config('DB_ENGINE', default='') == 'django.db.backends.mysql' else {},
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = get_config('LANGUAGE_CODE', default='fr-fr')
TIME_ZONE = get_config('TIME_ZONE', default='Europe/Paris')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication URLs
LOGIN_REDIRECT_URL = 'assets:dashboard'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'login'

# Email configuration
EMAIL_BACKEND = get_config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = get_config('EMAIL_HOST', default='')
EMAIL_PORT = get_config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = get_config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = get_config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = get_config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = get_config('DEFAULT_FROM_EMAIL', default='RadGestMat <noreply@radgestmat.local>')

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Session settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24 hours

# CSRF settings
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_COOKIE_SAMESITE = 'Lax'

# Django REST Framework (optional - uncomment when rest_framework is installed)
# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#         'rest_framework.authentication.SessionAuthentication',
#     ],
#     'DEFAULT_PERMISSION_CLASSES': [
#         'rest_framework.permissions.IsAuthenticated',
#     ],
#     'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
#     'PAGE_SIZE': 20,
#     'DEFAULT_FILTER_BACKENDS': [
#         'rest_framework.filters.SearchFilter',
#         'rest_framework.filters.OrderingFilter',
#     ],
#     'DEFAULT_RENDERER_CLASSES': [
#         'rest_framework.renderers.JSONRenderer',
#     ],
#     'DEFAULT_PARSER_CLASSES': [
#         'rest_framework.parsers.JSONParser',
#         'rest_framework.parsers.FormParser',
#         'rest_framework.parsers.MultiPartParser',
#     ],
# }

# CORS settings (for API access - uncomment when corsheaders is installed)
# CORS_ALLOWED_ORIGINS = get_csv(
#     'CORS_ALLOWED_ORIGINS',
#     default='http://localhost:3000,http://localhost:8000'
# )
# CORS_ALLOW_CREDENTIALS = True

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'radgestmat.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'ERROR',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': get_config('LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': get_config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'assets': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'users': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# QR Code domain configuration
QR_DOMAIN = get_config('QR_DOMAIN', default='http://localhost:8000')

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': get_config('CACHE_BACKEND', default='django.core.cache.backends.locmem.LocMemCache'),
        'LOCATION': get_config('CACHE_LOCATION', default=''),
    }
}

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB

