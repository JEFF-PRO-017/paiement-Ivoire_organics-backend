from apps.employes.models import Employe
from apps.odoo_attendance.models import Attendance
from rest_framework import serializers
from apps.employes.serializers import EmployeSerializer
from .models import Portefeuille, HistoriquePaiement

# TODO : A SUPPIMER
class PortefeuilleSerializer(serializers.ModelSerializer):
    employe      = EmployeSerializer(read_only=True)
    montant_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model  = Portefeuille
        fields = [
            'id', 'employe', 'nombre_jours_impayes', 'montant_journalier',
            'montant_total', 'periodes_paiement', 'statut', 'cree_le', 'modifie_le',
        ]
# ...........................................................

class HistoriquePaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model  = HistoriquePaiement
        fields = ['id', 'date_paiement', 'montant_total', 'nombre_jours', 'periodes_paiement','statut']



class EmployeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Employe
        fields = ['odoo_id', 'nom_complet', 'departement', 'site_travail', 'statut','mobile_phone']


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Attendance
        fields = '__all__'


class AttendanceParEmployeSerializer(serializers.Serializer):
    employe         = EmployeSerializer()
    attendance_list = AttendanceSerializer(many=True)