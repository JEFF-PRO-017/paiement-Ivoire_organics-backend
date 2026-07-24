from apps.paiements.models import ConfigurationPaiement
from apps.notch_pay.services.notchpay_service import consulter_solde
from rest_framework.views import APIView

from core.response import ApiResponse
from .serializers import ConfigurationPaiementSerializer
from .services.paiement_service import (
    creer_paiements_en_attente,
    executer_paiements,
    relancer_paiements_echoues,
)


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
        executer_paiements(paiements)

        return ApiResponse.success(
            data=_resume(paiements),
            message="Paiements traités"
        )


class RelancePaiementEchoueView(APIView):
    """POST {employe_ids: [...]?}: retente tous les paiements FAILED."""

    def post(self, request):
        employe_ids = request.data.get('employe_ids')
        paiements = relancer_paiements_echoues(employes=employe_ids)
        resume = {k: v for k, v in _resume(paiements).items() if k != 'total'}

        return ApiResponse.success(
            data={'total_relances': len(paiements), **resume},
            message="Relance effectuée"
        )


class SoldeNotchPayView(APIView):
    """GET: solde disponible sur le compte NotchPay, par devise."""

    def get(self, request):
        try:
            solde = consulter_solde()
        except Exception as e:
            return ApiResponse.error(
                message="Impossible de récupérer le solde NotchPay",
                errors=str(e),
                status_code=502,
                code="NOTCHPAY_UNAVAILABLE"
            )

        return ApiResponse.success(data={'solde': solde})