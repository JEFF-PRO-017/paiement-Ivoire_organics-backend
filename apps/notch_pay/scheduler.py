import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apps.notch_pay.services.paiement_service import executer_cycle_automatique

logger = logging.getLogger(__name__)

_scheduler = None


def _task_cycle_paiement_auto():
    """Vérifie chaque jour si le cycle de 15 jours est atteint (mode AUTOMATIQUE uniquement)."""
    logger.info("[Paiement] Vérification du cycle automatique...")
    executer_cycle_automatique()


def start():
    global _scheduler

    if _scheduler is not None:
        return  # évite un double démarrage (ex: rechargement auto de runserver)

    _scheduler = BackgroundScheduler()
    # interval en minutes : 1440 = 24h. On ne met pas 15 jours directement,
    # car c'est la fonction elle-même qui décide (via echeance_atteinte()) si elle doit agir.
    _scheduler.add_job(_task_cycle_paiement_auto, "interval", minutes=1440, id="cycle_paiement_auto")
    _scheduler.start()
    logger.info("[Paiement] Scheduler démarré — job cycle_paiement_auto actif.")