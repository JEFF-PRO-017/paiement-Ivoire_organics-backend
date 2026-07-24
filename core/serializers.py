from rest_framework import serializers


class PaginationSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)


class ApiResponseSerializer(serializers.Serializer):
    """Sérialiseur générique pour documenter le format standard des réponses."""
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.JSONField(allow_null=True)
    errors = serializers.JSONField(allow_null=True, required=False)
    code = serializers.CharField(allow_null=True, required=False)


class PaginatedResponseSerializer(ApiResponseSerializer):
    """Variante quand `data` contient results + pagination."""
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["data"] = {
            "results": instance["data"]["results"],
            "pagination": PaginationSerializer(instance["data"]["pagination"]).data
        }
        return rep