from apps.paiements.models import ConfigurationPaiement
from rest_framework.views import APIView

from apps.pawa_pay.client import consulter_solde
from core.response import ApiResponse
from .serializers import ConfigurationPaiementSerializer
from .services import creer_paiements_en_attente, executer_paiements


def _resume(paiements):
    return {
        'total': len(paiements),
        'reussis': sum(1 for p in paiements if p.statut == 'SUCCESS'),
        'echoues': sum(1 for p in paiements if p.statut == 'FAILED'),
        'en_attente': sum(1 for p in paiements if p.statut == 'PENDING'),
    }


class ConfigurationPaiementView(APIView):
    """GET: état actuel. POST {mode}: bascule MANUEL <-> AUTOMATIQUE."""

    def get(self, request):
        config = ConfigurationPaiement.get_instance()
        return ApiResponse.success(data=ConfigurationPaiementSerializer(config).data)

    def post(self, request):
        mode = request.data.get('mode')
        if mode not in ('MANUEL', 'AUTOMATIQUE'):
            return ApiResponse.error(
                message="Mode invalide",
                errors={"mode": ["Doit être 'MANUEL' ou 'AUTOMATIQUE'."]},
                status_code=400,
                code="INVALID_MODE"
            )

        config = ConfigurationPaiement.get_instance()
        config.passer_en_automatique() if mode == 'AUTOMATIQUE' else config.passer_en_manuel()

        return ApiResponse.success(
            data=ConfigurationPaiementSerializer(config).data,
            message=f"Mode {mode} activé"
        )


class PaiementManuelView(APIView):
    """POST {employe_ids: [...]?}: déclenche le paiement à la demande."""

    def post(self, request):
        employe_ids = request.data.get('employe_ids')
        paiements = creer_paiements_en_attente(employes=employe_ids, type_paiement='DEMANDE')
        response=executer_paiements(paiements)
        #mettre les exceptions dans un tableau pour les afficher dans le front
        return ApiResponse.success(
            data=response,
            message="Paiements traités"
        )


class SoldePawaPayView(APIView):
    """GET: solde disponible sur le compte PawaPay, par pays/devise."""

    def get(self, request):
        solde = consulter_solde()
        return ApiResponse.success(data={'solde': solde})