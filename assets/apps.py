from django.apps import AppConfig
import os
import sys


class AssetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'assets'
    
    def ready(self):
        # Skip signal imports during migrations
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return
        if os.environ.get('DISABLE_SIGNALS', '0') == '1':
            return
            
        import assets.signals  # Enregistrer les signaux
        # Signaux d'audit séparés
        try:
            import assets.signals_audit  # noqa: F401
        except Exception:
            # Avoid breaking startup if audit signals fail
            pass