from django.apps import AppConfig
import os


class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notch_pay'

    def ready(self):
        # RUN_MAIN évite que le scheduler démarre 2x avec `runserver` (qui lance 2 process : le reloader + le vrai serveur)
        if os.environ.get('RUN_MAIN') != 'true' and not os.environ.get('GUNICORN_CMD_ARGS'):
            return
        from . import scheduler
        scheduler.start()