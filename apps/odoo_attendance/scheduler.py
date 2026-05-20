"""
scheduler.py
────────────
Tâches planifiées — démarré une seule fois via apps.py ready().

  Au démarrage   : charge tous les employés
  Toutes 30 min  : nouveaux employés + nouvelles présences
"""

import logging
import socket
from apscheduler.schedulers.background import BackgroundScheduler

logger     = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_network_error(e: Exception) -> bool:
    """Retourne True si l'erreur est liée au réseau (pas un bug de code)."""
    network_errors = (
        OSError,
        ConnectionError,
        TimeoutError,
        socket.timeout,
        socket.gaierror,
    )
    return isinstance(e, network_errors) or "Network is unreachable" in str(e) \
           or "Connection timed out" in str(e) or "Errno 101" in str(e) \
           or "Errno 110" in str(e)


# ── Tâches ────────────────────────────────────────────────────────────────────

def _task_load_all_employees():
    from .odoo_service import get_all_employees
    from .services import save_employees
    try:
        records = get_all_employees()
        save_employees(records)
        logger.info(f"[Odoo] {len(records)} employés chargés au démarrage.")
    except Exception as e:
        if _is_network_error(e):
            logger.warning(
                f"[Odoo] Chargement employés ignoré : réseau inaccessible ({e}). "
                f"Vérifiez votre connexion ou VPN."
            )
        else:
            logger.error(f"[Odoo] Erreur chargement employés : {e}", exc_info=True)


def _task_sync_new_employees():
    from .odoo_service import get_new_employees
    from .services import save_employees
    try:
        records = get_new_employees(since_minutes=120)
        if records:
            save_employees(records)
            logger.info(f"[Odoo] {len(records)} nouvel(s) employé(s) synchronisé(s).")
    except Exception as e:
        if _is_network_error(e):
            logger.warning(
                f"[Odoo] Sync employés ignorée : réseau inaccessible ({e}). "
                f"Nouvelle tentative dans 120 min."
            )
        else:
            logger.error(f"[Odoo] Erreur sync employés : {e}", exc_info=True)


def _task_sync_new_attendances():
    from .odoo_service import get_new_attendances
    from .services import save_attendances
    try:
        records = get_new_attendances(since_minutes=120)
        if records:
            save_attendances(records)
            logger.info(f"[Odoo] {len(records)} présence(s) synchronisée(s).")
    except Exception as e:
        if _is_network_error(e):
            logger.warning(
                f"[Odoo] Sync présences ignorée : réseau inaccessible ({e}). "
                f"Nouvelle tentative dans 120 min."
            )
        else:
            logger.error(f"[Odoo] Erreur sync présences : {e}", exc_info=True)


def _task_load_all_attendances():
    from .odoo_service import get_last_days_attendances
    from .services import save_attendances
    try:
        records = get_last_days_attendances()
        print(f"Présences des 10 derniers jours : {len(records)}")
        save_attendances(records)
        logger.info(f"[Odoo] {len(records)} présences chargées au démarrage.")
    except Exception as e:
        if _is_network_error(e):
            logger.warning(
                f"[Odoo] Chargement présences ignoré : réseau inaccessible ({e}). "
                f"Vérifiez votre connexion ou VPN."
            )
        else:
            logger.error(f"[Odoo] Erreur chargement présences : {e}", exc_info=True)


# ── Démarrage ─────────────────────────────────────────────────────────────────

def start():
    """Appelé dans apps.py ready() — démarre une seule fois."""
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