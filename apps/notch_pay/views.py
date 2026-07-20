from apps.paiements.models import ConfigurationPaiement
from apps.notch_pay.services.notchpay_service import consulter_solde
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import ConfigurationPaiementSerializer
from .services.paiement_service import (
    creer_paiements_en_attente,
    executer_paiements,
    relancer_paiements_echoues,
)


def _resume(paiements):
    """Factorise le résumé retourné par les 3 vues de déclenchement de paiement."""
    return {
        'total': len(paiements),
        'reussis': sum(1 for p in paiements if p.statut == 'SUCCESS'),
        'echoues': sum(1 for p in paiements if p.statut == 'FAILED'),
        'en_attente': sum(1 for p in paiements if p.statut == 'PENDING'),
    }


class ConfigurationPaiementView(APIView):
    """GET: état actuel + jours restants. POST {mode}: bascule MANUEL <-> AUTOMATIQUE."""

    def get(self, request):
        config = ConfigurationPaiement.get_instance()
        return Response(ConfigurationPaiementSerializer(config).data)

    def post(self, request):
        mode = request.data.get('mode')
        if mode not in ('MANUEL', 'AUTOMATIQUE'):
            return Response({'erreur': 'mode invalide'}, status=status.HTTP_400_BAD_REQUEST)

        config = ConfigurationPaiement.get_instance()
        config.passer_en_automatique() if mode == 'AUTOMATIQUE' else config.passer_en_manuel()

        return Response(ConfigurationPaiementSerializer(config).data)


class PaiementManuelView(APIView):
    """POST {employe_ids: [...]?}: déclenche le paiement à la demande."""

    def post(self, request):
        employe_ids = request.data.get('employe_ids')
        paiements = creer_paiements_en_attente(employes=employe_ids, type_paiement='DEMANDE')
        executer_paiements(paiements)
        return Response(_resume(paiements))


class RelancePaiementEchoueView(APIView):
    """POST {employe_ids: [...]?}: retente tous les paiements FAILED."""

    def post(self, request):
        employe_ids = request.data.get('employe_ids')
        paiements = relancer_paiements_echoues(employes=employe_ids)
        return Response({'total_relances': len(paiements), **{k: v for k, v in _resume(paiements).items() if k != 'total'}})
    


class SoldeNotchPayView(APIView):
    """GET: solde disponible sur le compte NotchPay, par devise."""

    def get(self, request):
        try:
            solde = consulter_solde()
        except Exception as e:
            return Response({'erreur': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({'solde': solde})