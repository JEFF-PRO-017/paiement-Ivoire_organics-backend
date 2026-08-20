import logging
import requests
from django.conf import settings

# Client centralisé : toutes les fonctions PawaPay passent par ici
# pour ne pas répéter l'URL de base et les headers d'authentification.

logger = logging.getLogger(__name__)

BASE_URL = settings.PAWAPAY_BASE_URL


class PawaPayError(Exception):
    """Exception levée en cas d'échec d'un appel à l'API PawaPay."""
    pass


def _headers():
    return {
        "Authorization": f"Bearer {settings.PAWAPAY_API_TOKEN}",
        "Content-Type": "application/json",
    }


def consulter_solde():
    """Retourne la liste des soldes du wallet PawaPay (par pays/devise).

    Lève PawaPayError en cas d'échec, ce qui interrompt la procédure appelante.
    """
    url = f"{BASE_URL}/v2/wallet-balances"
    try:
        response = requests.get(url, headers=_headers(), timeout=15)
        response.raise_for_status()
        return response.json().get("balances", [])
    except requests.exceptions.RequestException as e:
        logger.error("Erreur lors de la consultation du solde PawaPay: %s", e)
        raise PawaPayError(f"Impossible de consulter le solde PawaPay: {e}") from e


def envoyer_bulk_payout(payload):
    """Envoie une liste de payouts à PawaPay en une seule requête bulk.

    Lève PawaPayError en cas d'échec, ce qui interrompt la procédure appelante.
    """
    url = f"{BASE_URL}/v2/payouts/bulk"
    try:
        response = requests.post(url, json=payload, headers=_headers(), timeout=30)
        response.raise_for_status()
        print('response bulk payout', response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error("Erreur lors de l'envoi du bulk payout PawaPay: %s", e)
        raise PawaPayError(f"Échec de l'envoi du bulk payout PawaPay: {e}") from e


def consulter_payout(payout_id):
    """Consulte le statut d'un payout spécifique sur PawaPay.

    Lève PawaPayError en cas d'échec, ce qui interrompt la procédure appelante.
    """
    url = f"{BASE_URL}/v2/payouts/{payout_id}"
    try:
        response = requests.get(url, headers=_headers(), timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Erreur lors de la consultation du payout %s: %s", payout_id, e)
        raise PawaPayError(f"Impossible de consulter le payout {payout_id}: {e}") from e