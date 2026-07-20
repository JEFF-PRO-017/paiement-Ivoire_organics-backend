from itertools import islice

from django.conf import settings
from django.utils import timezone

import notchpay
from notchpay.exceptions import (
    NotchPayValidationError, NotchPayAuthenticationError,
    NotchPayAPIError, NotchPayError,
)

TAILLE_MAX_BULK = 200  # limite imposée par NotchPay pour /transfers/bulk


def _client():
    notchpay.api_key = settings.NOTCHPAY_API_KEY
    notchpay.set_grant_key(settings.NOTCHPAY_GRANT_KEY)  # obligatoire pour les transfers
    return notchpay


def _mapper_statut(status_notchpay):
    """NotchPay renvoie 'complete'/'failed'/'pending' -> on aligne sur nos choices internes."""
    mapping = {'complete': 'SUCCESS', 'failed': 'FAILED', 'pending': 'PENDING'}
    return mapping.get(status_notchpay, 'PENDING')


def _decouper_en_tranches(liste, taille):
    """Découpe une liste en sous-listes de `taille` max (natif Python via itertools)."""
    it = iter(liste)
    while tranche := list(islice(it, taille)):
        yield tranche


def _construire_transfert(paiement):
    """Réutilise le beneficiary_id existant, sinon envoie les données brutes (création à la volée)."""
    base = {
        'amount': int(paiement.montant),
        'channel': paiement.methode_paiement,
        'reference': paiement.reference,
    }
    employe = paiement.employe

    if employe.notchpay_beneficiary_id:
        base['beneficiary'] = employe.notchpay_beneficiary_id
    else:
        base['beneficiary_data'] = {
            'name': employe.nom_complet,
            'phone': str(paiement.phone_number),
        }
    return base


def _appliquer_resultats_bulk(bulk, paiements_par_reference):
    """Répartit la réponse du lot sur chaque Paiement + mémorise le beneficiary_id créé."""
    for resultat in bulk.transfers:
        paiement = paiements_par_reference.get(resultat.reference)
        if not paiement:
            continue

        paiement.transaction_id = resultat.id
        paiement.bulk_transfer_id = bulk.id
        paiement.statut = _mapper_statut(resultat.status)
        if paiement.statut != 'PENDING':
            paiement.date_confirmation = timezone.now()
        paiement.save()

        employe = paiement.employe
        if not employe.notchpay_beneficiary_id and getattr(resultat, 'beneficiary', None):
            employe.notchpay_beneficiary_id = resultat.beneficiary
            employe.save(update_fields=['notchpay_beneficiary_id'])


def _envoyer_lot(paiements):
    """Envoie un seul lot (<= 200 paiements, 1 inclus) en une requête bulk NotchPay."""
    client = _client()
    paiements_par_reference = {p.reference: p for p in paiements}

    for p in paiements:
        p.date_envoi = timezone.now()
        p.nombre_tentatives += 1

    try:
        response = client.transfers.create_bulk({
            'currency': 'XOF',
            'description': f"Paie du {timezone.now().date()}",
            'transfers': [_construire_transfert(p) for p in paiements],
        })
        _appliquer_resultats_bulk(response.bulk_transfer, paiements_par_reference)

    except NotchPayValidationError as e:
        for p in paiements:
            p.statut = 'FAILED'
            p.message_erreur = str(e.errors)
            p.date_confirmation = timezone.now()
            p.save()

    except (NotchPayAuthenticationError, NotchPayAPIError, NotchPayError) as e:
        for p in paiements:
            p.statut = 'FAILED'
            p.message_erreur = str(e)
            p.date_confirmation = timezone.now()
            p.save()

    return paiements


def envoyer_transfert(paiements):
    """
    Point d'entrée unique, quel que soit le volume : 1 paiement ou 500.
    Découpe automatiquement en tranches de 200 (limite NotchPay) et envoie chaque tranche en bulk.
    """
    for tranche in _decouper_en_tranches(paiements, TAILLE_MAX_BULK):
        _envoyer_lot(tranche)
    return paiements


def verifier_statut_bulk(bulk_transfer_id):
    """Poll un lot entier (statut initial souvent 'Accepted'/202, à re-vérifier plus tard)."""
    from apps.paiements.models import Paiement  # import local pour éviter une dépendance circulaire

    client = _client()
    response = client.transfers.retrieve_bulk(bulk_transfer_id)
    bulk = response.bulk_transfer

    for resultat in bulk.transfers:
        try:
            paiement = Paiement.objects.get(reference=resultat.reference)
        except Paiement.DoesNotExist:
            continue
        paiement.statut = _mapper_statut(resultat.status)
        if paiement.statut != 'PENDING':
            paiement.date_confirmation = timezone.now()
        paiement.save()


def consulter_solde():
    """Vérifie le solde disponible sur le compte NotchPay avant d'envoyer un gros lot."""
    client = _client()
    response = client.balance.retrieve()
    return response.balance.available  # dict {currency: montant}