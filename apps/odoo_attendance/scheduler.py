"""
scheduler.py
────────────
Tâches planifiées — démarré une seule fois via apps.py ready().

  Au démarrage   : charge tous les employés + présences
  Toutes 120 min : nouveaux employés + nouvelles présences
"""

import logging
import socket
from django.conf import settings
from apscheduler.schedulers.background import BackgroundScheduler
from .odoo_service import OdooConnectionError, OdooAuthError, OdooDataError

logger     = logging.getLogger(__name__)
IS_DEV     = settings.DEBUG
_scheduler: BackgroundScheduler | None = None


# ── Utils ─────────────────────────────────────────────────────────────────────

def _dev(msg: str):
    """Print uniquement en mode DEBUG (développement)."""
    if IS_DEV:
        print(f"[DEV] {msg}")


def _handle_odoo_error(context: str, e: Exception):
    """Gestion centralisée des erreurs Odoo — log propre, pas de traceback sauvage."""
    if isinstance(e, OdooConnectionError):
        logger.warning(f"[Odoo] {context} — réseau inaccessible : {e}")
        _dev(f"{context} ignoré (réseau). Vérifiez Odoo/VPN.")
    elif isinstance(e, OdooAuthError):
        logger.error(f"[Odoo] {context} — authentification échouée : {e}")
        _dev(f"{context} ECHEC AUTH — vérifiez ODOO_USERNAME / ODOO_PASSWORD dans .env")
    elif isinstance(e, OdooDataError):
        logger.error(f"[Odoo] {context} — données invalides : {e}")
        _dev(f"{context} ECHEC DATA — réponse Odoo malformée (voir logs)")
    else:
        logger.error(f"[Odoo] {context} — erreur inattendue : {e}", exc_info=IS_DEV)
        _dev(f"{context} ERREUR INCONNUE : {e}")


# ── Tâches ────────────────────────────────────────────────────────────────────

def _task_load_all_employees():
    from .odoo_service import get_all_employees
    from .services import save_employees
    _dev(">>> Chargement initial des employés...")
    try:
        records = get_all_employees()
        save_employees(records)
        logger.info(f"[Odoo] {len(records)} employés chargés au démarrage.")
        _dev(f"<<< {len(records)} employés chargés OK.")
    except Exception as e:
        _handle_odoo_error("Chargement employés", e)


def _task_load_all_attendances():
    from .odoo_service import get_last_days_attendances
    from .services import save_attendances
    _dev(">>> Chargement initial des présences (15 derniers jours)...")
    try:
        records = get_last_days_attendances()
        save_attendances(records)
        logger.info(f"[Odoo] {len(records)} présences chargées au démarrage.")
        _dev(f"<<< {len(records)} présences chargées OK.")
    except Exception as e:
        _handle_odoo_error("Chargement présences", e)


def _task_sync_new_employees():
    from .odoo_service import get_new_employees
    from .services import save_employees
    _dev(">>> Sync nouveaux employés...")
    try:
        records = get_new_employees(since_minutes=120)
        if records:
            save_employees(records)
            logger.info(f"[Odoo] {len(records)} nouvel(s) employé(s) synchronisé(s).")
            _dev(f"<<< {len(records)} nouveaux employés synchronisés.")
        else:
            logger.debug("[Odoo] Sync employés : aucun nouveau.")
            _dev("<<< Aucun nouvel employé.")
    except Exception as e:
        _handle_odoo_error("Sync employés", e)


def _task_sync_new_attendances():
    from .odoo_service import get_new_attendances
    from .services import save_attendances
    _dev(">>> Sync nouvelles présences...")
    try:
        records = get_new_attendances(since_minutes=120)
        if records:
            save_attendances(records)
            logger.info(f"[Odoo] {len(records)} présence(s) synchronisée(s).")
            _dev(f"<<< {len(records)} présences synchronisées.")
        else:
            logger.debug("[Odoo] Sync présences : aucune nouvelle.")
            _dev("<<< Aucune nouvelle présence.")
    except Exception as e:
        _handle_odoo_error("Sync présences", e)


# ── Démarrage ─────────────────────────────────────────────────────────────────

def start():
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_task_load_all_employees,   "date",     id="init_employees")
    _scheduler.add_job(_task_load_all_attendances, "date",     id="init_attendances")
    _scheduler.add_job(_task_sync_new_employees,   "interval", minutes=120, id="sync_employees")
    _scheduler.add_job(_task_sync_new_attendances, "interval", minutes=120, id="sync_attendances")
    _scheduler.start()
    logger.info("[Odoo] Scheduler démarré.")
    _dev("Scheduler APScheduler démarré — 4 jobs actifs.")