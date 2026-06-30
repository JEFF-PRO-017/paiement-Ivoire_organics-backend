from functools import wraps
from apps.front_settings.services import ParametreService


def avec_parametres(vue):
    """
    Décorateur pour vues DRF. Injecte `request.parametres` (dict prêt
    à l'emploi) en se basant uniquement sur le user connecté.

    Usage :
        @avec_parametres
        def ma_vue(request):
            request.parametres['mode']  # 'CLAIR' ou 'SOMBRE'
    """
    @wraps(vue)
    def wrapper(request, *args, **kwargs):
        parametre = ParametreService.get_ou_creer(request.user)
        request.parametres = parametre.to_dict()
        return vue(request, *args, **kwargs)
    return wrapper