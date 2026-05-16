from rest_framework import serializers
from .models import Employe


class EmployeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Employe
        fields = ['id', 'odoo_id', 'nom_complet', 'departement', 'site_travail', 'statut']
