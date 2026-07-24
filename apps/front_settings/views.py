from rest_framework import generics
from rest_framework.mixins import UpdateModelMixin

from core.response import ApiResponse
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

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return ApiResponse.success(
            data=serializer.data,
            message="Paramètres mis à jour avec succès"
        )