from apps.accounts.models import CustomUser
from .models import Parametre


class ParametreService:
    """Toute la logique métier autour de Parametre — un seul par user."""

    @staticmethod
    def get_ou_creer(user: CustomUser) -> Parametre:
        obj, _ = Parametre.objects.get_or_create(user=user)
        return obj

    @staticmethod
    def mettre_a_jour(parametre: Parametre, data: dict) -> Parametre:
        """Patch partiel — ne touche que les clés présentes dans data."""
        parametre.zoom = data.get('zoom', parametre.zoom)
        parametre.mode = data.get('mode', parametre.mode)
        parametre.site = data.get('site', parametre.site)

        dashboard = data.get('page_dashboard', {})
        parametre.dashboard_composant_1 = dashboard.get('composant_1', parametre.dashboard_composant_1)
        parametre.dashboard_composant_2 = dashboard.get('composant_2', parametre.dashboard_composant_2)
        parametre.dashboard_composant_3 = dashboard.get('composant_3', parametre.dashboard_composant_3)
        parametre.dashboard_composant_4 = dashboard.get('composant_4', parametre.dashboard_composant_4)

        detail = data.get('page_detail', {})
        parametre.detail_composant_1 = detail.get('composant_1', parametre.detail_composant_1)
        parametre.detail_composant_2 = detail.get('composant_2', parametre.detail_composant_2)
        parametre.detail_composant_3 = detail.get('composant_3', parametre.detail_composant_3)
        parametre.detail_composant_4 = detail.get('composant_4', parametre.detail_composant_4)

        historique = data.get('page_historique', {})
        parametre.historique_composant_1 = historique.get('composant_1', parametre.historique_composant_1)
        parametre.historique_composant_2 = historique.get('composant_2', parametre.historique_composant_2)
        parametre.historique_composant_3 = historique.get('composant_3', parametre.historique_composant_3)

        parametre.save()
        return parametre