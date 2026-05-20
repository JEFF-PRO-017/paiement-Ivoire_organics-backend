from django.apps import AppConfig


class OdooAttendanceConfig(AppConfig):
    name    = "apps.odoo_attendance"
    verbose_name = "Synchronisation Odoo"

    def ready(self):
        # Évite le double démarrage en mode dev (reloader)
        import os
        # if os.environ.get("RUN_MAIN") != "true":
        #     return
        from .scheduler import start
        start()