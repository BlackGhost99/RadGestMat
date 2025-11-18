"""
Settings module for RadGestMat
Loads appropriate settings based on environment
"""
import os

# Try to use decouple, fallback to os.environ if not available
try:
    from decouple import config
    ENVIRONMENT = config('ENVIRONMENT', default='development')
except ImportError:
    # Fallback if decouple is not installed
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'staging':
    from .staging import *
else:
    from .development import *

