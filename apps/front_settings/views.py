from rest_framework import generics, permissions

from .models import Parametre
from .serializers import ParametreSerializer
from .services import ParametreService


class ParametreUpdateView(generics.UpdateAPIView):
    """PATCH /api/parametres/ — met à jour les préférences du user connecté."""

    serializer_class = ParametreSerializer
    http_method_names = ['patch']

    def get_object(self) -> Parametre:
        return ParametreService.get_ou_creer(self.request.user)

    def perform_update(self, serializer):
        ParametreService.mettre_a_jour(serializer.instance, self.request.data)