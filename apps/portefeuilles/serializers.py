from rest_framework import serializers
from apps.employes.serializers import EmployeSerializer
from .models import Portefeuille, HistoriquePaiement


class PortefeuilleSerializer(serializers.ModelSerializer):
    employe      = EmployeSerializer(read_only=True)
    montant_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model  = Portefeuille
        fields = [
            'id', 'employe', 'nombre_jours_impayes', 'montant_journalier',
            'montant_total', 'periodes_paiement', 'statut', 'cree_le', 'modifie_le',
        ]


class HistoriquePaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model  = HistoriquePaiement
        fields = ['id', 'date_paiement', 'montant_total', 'nombre_jours']
