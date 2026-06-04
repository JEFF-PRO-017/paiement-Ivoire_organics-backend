from django.apps import AppConfig


class OdooAttendanceConfig(AppConfig):
    name = "apps.odoo_attendance"
    verbose_name = "Synchronisation Odoo"

    def ready(self):
        import os

        # Ne lance le scheduler que si explicitement activé
        if os.environ.get("SCHEDULER_ENABLED") != "true":
            return

        # Évite le double démarrage en mode dev (reloader)
        if os.environ.get("RUN_MAIN") == "false":
            return

        from .scheduler import start
        start()