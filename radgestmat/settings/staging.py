"""
Staging settings for RadGestMat
Similar to production but with some debugging enabled
"""
import os
from .production import *

try:
    from decouple import config
    DEBUG = config('DEBUG', default=False, cast=bool)
except ImportError:
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Allow more hosts in staging
try:
    from decouple import config, Csv
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
except ImportError:
    import os
    ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]

# Security settings - Can be relaxed slightly for staging
try:
    from decouple import config
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
except ImportError:
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'True').lower() == 'true'

# Logging - More verbose in staging
LOGGING['root']['level'] = 'DEBUG'

