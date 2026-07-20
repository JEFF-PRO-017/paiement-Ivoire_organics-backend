from apps.paiements.models import ConfigurationPaiement
from rest_framework import serializers


class ConfigurationPaiementSerializer(serializers.ModelSerializer):
    jours_restants = serializers.SerializerMethodField()

    class Meta:
        model = ConfigurationPaiement
        fields = ['mode', 'date_changement_mode', 'derniere_execution_auto', 'jours_restants']

    def get_jours_restants(self, obj):
        return obj.jours_restants()