from django.db.models import Sum
from django.utils import timezone

from apps.accounts.models import Site
from apps.odoo_attendance.models import Attendance
from apps.paiements.models import ConfigurationPaiement, Paiement
from apps.pawa_pay.client import consulter_payout, envoyer_bulk_payout
from django.conf import settings


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
        )
        paiement.attendances.set(attendances)
        paiements.append(paiement)

    return paiements


def _construire_payload_bulk(paiements):
    """Transforme une liste de Paiement Django en JSON attendu par POST /v2/payouts/bulk."""
    payload = []

    for paiement in paiements:
        provider = paiement.methode_paiement
        #si je suis en mode debug le prix c'est 15 sinon c'est le vrai
        amount = str(paiement.montant) if not settings.DEBUG else "15"  
        payload.append({
            "payoutId": paiement.reference,
            "amount": amount,
            "currency": "XOF",
            "clientReferenceId": paiement.employe.clientReferenceId,
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
    Le statut final (ACCEPTED/REJECTED/DUPLICATE_IGNORED) arrive plus tard via le callback.
    """
    if not paiements:
        return None

    payload = _construire_payload_bulk(paiements)
    payouts = envoyer_bulk_payout(payload)

    for payout in payouts:
        paiement = Paiement.objects.get(reference=payout.get('payoutId'))
        if payout.get('status') == 'ACCEPTED':
            paiement.mettre_a_jour_statut('ENCOURS')
            paiement.date_envoi = timezone.now()
            paiement.reponse_brute = payout
        else :
            paiement.mettre_a_jour_statut('FAILED')
            paiement.date_envoi = timezone.now()
            paiement.reponse_brute = payout
        paiement.save()  

    return payouts


def executer_cycle_automatique():
    """A appeler chaque jour (scheduler). Agit sur chaque site en mode AUTOMATIQUE dont l'échéance est atteinte."""
    for site in Site.objects.all():
        _executer_cycle_automatique_pour_site(site)


def _executer_cycle_automatique_pour_site(site):
    config = ConfigurationPaiement.get_instance(site)
    if config.mode != 'AUTOMATIQUE' or not config.echeance_atteinte():
        return
    print(f"[DEV] executer_cycle_automatique : site={site.nom} mode={config.mode} échéance_atteinte={config.echeance_atteinte()}")
    paiements = creer_paiements_en_attente(type_paiement='AUTOMATIQUE', site=site)
    executer_paiements(paiements)
    config.derniere_execution_auto = timezone.now()
    config.save()
    #TODO : VERIFIER LE BON FONCTIONNEMENT APRES ET AVANT LE L'EXECTUSION

def callback_paiement_status_automatique():
    """
    Vérifie le statut des paiements en cours (ENCOURS) et met à jour leur statut final (ACCEPTED/ENQUEUED/PROCESSING/IN_RECONCILIATION/COMPLETED/FAILED).
    À appeler régulièrement (scheduler).
    """
    paiements_en_cours = Paiement.objects.filter(statut='ENCOURS')
    #TODO : VERIFIER LE BON FONCTIONNEMENT APRES ET AVANT LE L'EXECTUSION
    print(f"[DEV] callback_paiement_status_automatique : {paiements_en_cours.count()} paiements en cours à vérifier.")
    for paiement in paiements_en_cours:
        reponse = consulter_payout(paiement.reference)
        data = reponse.get('data', {})
        statut = data.get('status')
        if statut =='FOUND':
            if data.status == 'COMPLETED':
                paiement.mettre_a_jour_statut('SUCCESS')
                paiement.reponse_brute = reponse

            elif data.status == 'FAILED':
                paiement.mettre_a_jour_statut('FAILED') 
                paiement.reponse_brute = reponse
            paiement.save()
