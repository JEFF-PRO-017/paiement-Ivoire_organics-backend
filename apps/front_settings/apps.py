from django.apps import AppConfig

class FrontSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.front_settings'  # doit matcher le chemin réel

    def ready(self):
        import apps.front_settings.signals  # noqa: F401