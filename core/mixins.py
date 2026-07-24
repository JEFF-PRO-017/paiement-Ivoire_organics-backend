from functools import wraps

from apps.front_settings.services import ParametreService
from rest_framework.exceptions import ValidationError
# from utils.pagination import StandardPagination


# Pour les vues generics (ListAPIView...) : ajoute self.site automatiquement
class AvecSiteMixin:
    site_requis = True  # False = liste vide si pas de site, au lieu d'une erreur

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        parametre = ParametreService.get_ou_creer(request.user)
        request.parametres = parametre.to_dict()
        self.site = request.parametres.get('site')

        if not self.site and self.site_requis:
            raise ValidationError({'error': 'Site introuvable.'})


# Pour les vues APIView classiques : ajoute "site" en argument de la méthode
def avec_site(on_site_manquant=None):
    def decorateur(vue):
        @wraps(vue)
        def wrapper(self, request, *args, **kwargs):
            parametre = ParametreService.get_ou_creer(request.user)
            request.parametres = parametre.to_dict()
            site = request.parametres.get('site')

            # pas de site -> réponse custom si fournie, sinon erreur 400
            if not site:
                if on_site_manquant:
                    return on_site_manquant(self, request, *args, **kwargs)
                raise ValidationError({'error': 'Site introuvable.'})

            return vue(self, request, *args, site=site, **kwargs)
        return wrapper
    return decorateur


# Pagine une liste/queryset "à la main" (hors ListAPIView)
# def paginate(request, queryset, serializer_class=None):
#     paginator = StandardPagination()
#     page = paginator.paginate_queryset(queryset, request)
#     data = serializer_class(page, many=True).data if serializer_class else page
#     return paginator.get_paginated_response(data)