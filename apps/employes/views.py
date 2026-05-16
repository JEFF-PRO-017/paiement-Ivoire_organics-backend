from rest_framework import generics, filters
from .models import Employe
from .serializers import EmployeSerializer


class EmployeListView(generics.ListAPIView):
    queryset         = Employe.objects.filter(statut='ACTIF').order_by('nom_complet')
    serializer_class = EmployeSerializer
    filter_backends  = [filters.SearchFilter]
    search_fields    = ['nom_complet', 'odoo_id', 'departement']


class EmployeDetailView(generics.RetrieveAPIView):
    queryset         = Employe.objects.all()
    serializer_class = EmployeSerializer
