from django.apps import AppConfig


class AssetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'assets'
    
    def ready(self):
        import assets.signals  # Enregistrer les signaux
        # Signaux d'audit séparés
        try:
            import assets.signals_audit  # noqa: F401
        except Exception:
            # Avoid breaking startup if audit signals fail
            pass