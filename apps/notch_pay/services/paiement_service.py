import uuid

from django.db.models import Sum
from django.utils import timezone

from apps.odoo_attendance.models import Attendance
from apps.paiements.models import ConfigurationPaiement, Paiement

from . import notchpay_service


def creer_paiements_en_attente(employes=None, type_paiement='DEMANDE'):
    """Regroupe les attendances impayées par employé -> 1 virement par employé."""
    qs = Attendance.objects.filter(statut_paiement='EN_ATTENTE')
    if employes is not None:
        qs = qs.filter(employe__in=employes)

    paiements = []
    for employe_id in qs.values_list('employe_id', flat=True).distinct():
        attendances = qs.filter(employe_id=employe_id)
        employe = attendances.first().employe

        if not employe.mobile_phone or not employe.operateur_mobile:
            continue

        montant = attendances.aggregate(total=Sum('montant_journalier'))['total']

        paiement = Paiement.objects.create(
            employe=employe,
            date_paiement=timezone.now().date(),
            montant=montant,
            phone_number=employe.mobile_phone,
            methode_paiement=employe.operateur_mobile,
            type_paiement=type_paiement,
            statut='PENDING',
        )
        paiement.attendances.set(attendances)
        paiements.append(paiement)

    return paiements


def executer_paiements(paiements):
    """Envoie tous les paiements (1 seul ou des centaines) via le point d'entrée unique NotchPay."""
    if not paiements:
        return paiements

    notchpay_service.envoyer_transfert(paiements)

    for paiement in paiements:
        if paiement.statut == 'SUCCESS':
            paiement.attendances.update(
                statut_paiement='PAYE',
                date_validation_paiement=timezone.now(),
            )
    return paiements


def relancer_paiements_echoues(employes=None):
    """Reprend les Paiement FAILED avec une nouvelle référence (NotchPay rejette les références déjà utilisées)."""
    qs = Paiement.objects.filter(statut='FAILED')
    if employes is not None:
        qs = qs.filter(employe__in=employes)

    paiements = list(qs)
    for paiement in paiements:
        paiement.reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        paiement.statut = 'PENDING'
        paiement.save(update_fields=['reference', 'statut'])

    executer_paiements(paiements)
    return paiements


def executer_cycle_automatique():
    """A appeler chaque jour (scheduler). Agit seulement si mode AUTOMATIQUE + échéance des 15j atteinte."""
    config = ConfigurationPaiement.get_instance()
    if config.mode != 'AUTOMATIQUE' or not config.echeance_atteinte():
        return

    paiements = creer_paiements_en_attente(type_paiement='AUTOMATIQUE')
    executer_paiements(paiements)
    config.derniere_execution_auto = timezone.now()
    config.save()