from django.apps import AppConfig
import os


class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.pawa_pay'

    def ready(self):
        if os.environ.get("VERCEL"):
            return

        if os.environ.get("RUN_MAIN") == "false":
            return

        import threading
        from .scheduler import start

        def delayed_start():
            import time
            time.sleep(60)
            start()

        thread = threading.Thread(target=delayed_start, daemon=True)
        thread.start()