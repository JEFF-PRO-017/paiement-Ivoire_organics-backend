"""
Planificateur qui exécute `executer_cycle_automatique` une fois par jour.
Nécessite le package `apscheduler` (pip install apscheduler).
"""
from apscheduler.schedulers.background import BackgroundScheduler

from .services import callback_paiement_status_automatique, executer_cycle_automatique


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(executer_cycle_automatique,trigger='interval',minutes=2,id='cycle_paiement_automatique',replace_existing=True,), #TODO : A REMETTRE A JOUR  
    scheduler.add_job(callback_paiement_status_automatique, trigger='interval', minutes=0.30, id='callback_paiement_status_automatique', replace_existing=True)
    scheduler.start()
    print("Scheduler pawa_pay démarré — 2 jobs actifs.")