from django.apps import AppConfig


class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.pawa_pay'

    def ready(self):
        import os

        # if os.environ.get("SCHEDULER_ENABLED") != "true":
        #     return

        if os.environ.get("RUN_MAIN") == "false":
            return

        import threading
        from .scheduler import start

        def delayed_start():
            import time
            time.sleep(60)  # attendre 1 minute
            start()

        thread = threading.Thread(target=delayed_start, daemon=True)
        thread.start()