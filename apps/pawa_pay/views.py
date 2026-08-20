from apps.paiements.models import ConfigurationPaiement
from apps.accounts.models import Site
from rest_framework.views import APIView

from apps.pawa_pay.client import consulter_solde
from core.mixins import avec_site
from core.response import ApiResponse
from .serializers import ConfigurationPaiementSerializer
from .services import callback_paiement_status_automatique, creer_paiements_en_attente, executer_paiements
from django.shortcuts import get_object_or_404


def _resume(paiements):
    return {
        'total': len(paiements),
        'reussis': sum(1 for p in paiements if p.statut == 'SUCCESS'),
        'echoues': sum(1 for p in paiements if p.statut == 'FAILED'),
        'en_attente': sum(1 for p in paiements if p.statut == 'ENCOURS'),
    }

class ConfigurationPaiementView(APIView):
    """GET: état actuel du site. POST {mode}: bascule MANUEL <-> AUTOMATIQUE."""

    @avec_site()
    def get(self, request, site):
        site_obj = get_object_or_404(Site, nom=site)
        print("site_obj",site_obj)
        config = ConfigurationPaiement.get_instance(site_obj)
        print("config",config)
        return ApiResponse.success(data=ConfigurationPaiementSerializer(config).data)

    @avec_site()
    def post(self, request, site):
        mode = request.data.get('mode')
        if mode not in ('MANUEL', 'AUTOMATIQUE'):
            return ApiResponse.error(
                message="Mode invalide",
                errors={"mode": ["Doit être 'MANUEL' ou 'AUTOMATIQUE'."]},
                status_code=400,
                code="INVALID_MODE"
            )

        site_obj = get_object_or_404(Site,nom=site)
        config = ConfigurationPaiement.get_instance(site_obj)
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


class VerifierPaiementsEnCoursView(APIView):
    def get(self, request):
        callback_paiement_status_automatique()
        return ApiResponse.success(message="Vérification des paiements en cours terminée.")