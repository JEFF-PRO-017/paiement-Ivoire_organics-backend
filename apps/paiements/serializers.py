from rest_framework import serializers
from apps.odoo_attendance.models import Attendance, Employe
from .models import HistoriquePaiement


class EmployeSerializer(serializers.ModelSerializer):
    """Sérialise un employé (lecture seule, utilisé en sous-objet)."""
    class Meta:
        model  = Employe
        fields = '__all__'


class AttendanceSerializer(serializers.ModelSerializer):
    """Sérialise une attendance complète (détail)."""
    class Meta:
        model  = Attendance
        fields = '__all__'


class AttendanceParEmployeSerializer(serializers.Serializer):
    """Regroupe les attendances par employé (utilisé pour la liste paginée)."""
    employe         = EmployeSerializer()
    attendance_list = AttendanceSerializer(many=True)


class HistoriquePaiementSerializer(serializers.ModelSerializer):
    """Sérialise une ligne d'historique de paiement."""
    class Meta:
        model  = HistoriquePaiement
        fields = '__all__'