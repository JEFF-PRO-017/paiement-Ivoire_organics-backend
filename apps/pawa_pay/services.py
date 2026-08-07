from django.db.models import Sum
from django.utils import timezone

from apps.odoo_attendance.models import Attendance
from apps.paiements.models import ConfigurationPaiement, Paiement
from apps.pawa_pay.client import consulter_payout, envoyer_bulk_payout


def creer_paiements_en_attente(employes=None, type_paiement='DEMANDE'):
    """Regroupe les attendances impayées par employé -> 1 virement par employé."""
    qs = Attendance.objects.filter(statut_paiement='IMPAYE')

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


def _construire_payload_bulk(paiements):
    """Transforme une liste de Paiement Django en JSON attendu par POST /v2/payouts/bulk."""
    payload = []

    for paiement in paiements:
        provider = paiement.methode_paiement
        payload.append({
            "payoutId": paiement.reference,
            # "amount": str(paiement.montant), #TODO REMETTRE APRES LA VRAI VALUE
            "amount": "15", #TODO: A SUPPRIMER, C'EST POUR TESTER
            "currency": "XOF",
            "recipient": {
                "type": "MMO",
                "accountDetails": {
                    "provider": provider,
                    "phoneNumber": str(paiement.phone_number).replace('+', ''),
                }
            },
            "customerMessage": "Paiement salaire",
            "metadata": [
                {"orderId": paiement.reference},
            ],
        })

    return payload


def executer_paiements(paiements):
    """
    Envoie les paiements à PawaPay et passe leur statut à ENCOURS.
    Le statut final (SUCCESS/FAILED) arrive plus tard via le callback.
    """
    if not paiements:
        return None

    payload = _construire_payload_bulk(paiements)
    payouts = envoyer_bulk_payout(payload)

     #TODO: VERIFIER LES CODES DE RETOUR DE L'API PAWAPAY

    for payout in payouts:
        if payout.get('status') != 'SUCCESS':
            continue
        paiement = Paiement.objects.get(reference=payout.get('payoutId'))
        paiement.statut = 'ENCOURS'
        paiement.date_envoi = timezone.now()
        paiement.reponse_brute = payout
        paiement.save()

    return payouts


def executer_cycle_automatique():
    """A appeler chaque jour (scheduler). Agit seulement si mode AUTOMATIQUE + échéance atteinte."""
    config = ConfigurationPaiement.get_instance()
    if config.mode != 'AUTOMATIQUE' or not config.echeance_atteinte():
        return

    paiements = creer_paiements_en_attente(type_paiement='AUTOMATIQUE')
    executer_paiements(paiements)
    config.derniere_execution_auto = timezone.now()
    config.save()

def callback_paiement_status_automatique():
    """
    Vérifie le statut des paiements en cours (ENCOURS) et met à jour leur statut final (SUCCESS/FAILED).
    À appeler régulièrement (scheduler).
    """
    paiements_en_cours = Paiement.objects.filter(statut='ENCOURS')

    for paiement in paiements_en_cours:
        reponse = consulter_payout(paiement.reference) #TODO: VERIFIER LES CODES DE RETOUR DE L'API PAWAPAY
        statut = reponse.get('status')
        if statut == 'SUCCESS':
            paiement.mettre_a_jour_statut('SUCCESS')
        elif statut == 'FAILED':
            paiement.mettre_a_jour_statut('FAILED')