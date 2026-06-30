from rest_framework import serializers
from .models import Parametre


class PageDashboardSerializer(serializers.Serializer):
    composant_1 = serializers.BooleanField(required=False)
    composant_2 = serializers.BooleanField(required=False)
    composant_3 = serializers.BooleanField(required=False)
    composant_4 = serializers.BooleanField(required=False)


class PageDetailSerializer(serializers.Serializer):
    composant_1 = serializers.BooleanField(required=False)
    composant_2 = serializers.BooleanField(required=False)
    composant_3 = serializers.BooleanField(required=False)
    composant_4 = serializers.BooleanField(required=False)


class PageHistoriqueSerializer(serializers.Serializer):
    composant_1 = serializers.BooleanField(required=False)
    composant_2 = serializers.BooleanField(required=False)
    composant_3 = serializers.BooleanField(required=False)


class ParametreSerializer(serializers.ModelSerializer):
    """
    Expose/accepte la forme imbriquée { zoom, mode, site, page_dashboard: {...}, ... }
    en mappant vers les champs plats du modèle.
    """
    page_dashboard  = PageDashboardSerializer(required=False)
    page_detail     = PageDetailSerializer(required=False)
    page_historique = PageHistoriqueSerializer(required=False)

    class Meta:
        model = Parametre
        fields = ['id', 'site', 'zoom', 'mode', 'page_dashboard', 'page_detail', 'page_historique']
        read_only_fields = ['id', 'site']  # le site identifie l'objet, non modifiable via patch

    def to_representation(self, instance):
        # Réutilise to_dict() du modèle pour rester sur une seule source de vérité
        data = instance.to_dict()
        data['id'] = instance.id
        return data

    def update(self, instance, validated_data):
        instance.zoom = validated_data.get('zoom', instance.zoom)
        instance.mode = validated_data.get('mode', instance.mode)

        dashboard = validated_data.get('page_dashboard', {})
        instance.dashboard_composant_1 = dashboard.get('composant_1', instance.dashboard_composant_1)
        instance.dashboard_composant_2 = dashboard.get('composant_2', instance.dashboard_composant_2)
        instance.dashboard_composant_3 = dashboard.get('composant_3', instance.dashboard_composant_3)
        instance.dashboard_composant_4 = dashboard.get('composant_4', instance.dashboard_composant_4)

        detail = validated_data.get('page_detail', {})
        instance.detail_composant_1 = detail.get('composant_1', instance.detail_composant_1)
        instance.detail_composant_2 = detail.get('composant_2', instance.detail_composant_2)
        instance.detail_composant_3 = detail.get('composant_3', instance.detail_composant_3)
        instance.detail_composant_4 = detail.get('composant_4', instance.detail_composant_4)

        historique = validated_data.get('page_historique', {})
        instance.historique_composant_1 = historique.get('composant_1', instance.historique_composant_1)
        instance.historique_composant_2 = historique.get('composant_2', instance.historique_composant_2)
        instance.historique_composant_3 = historique.get('composant_3', instance.historique_composant_3)

        instance.save()
        return instance