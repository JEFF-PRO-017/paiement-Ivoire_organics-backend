from rest_framework import serializers


# ── ENTRÉE ────────────────────────────────────────────────────────────────────

class UpdateStatutInputDTO(serializers.Serializer):
    """Données attendues pour mettre à jour le statut de plusieurs attendances."""
    ids               = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    statut_paiement   = serializers.CharField(required=False, allow_null=True)
    statut_attendance = serializers.CharField(required=False, allow_null=True)


class CreateAttendanceManuelInputDTO(serializers.Serializer):
    """Données attendues pour créer une attendance manuellement."""
    employee_id     = serializers.DecimalField(max_digits=10, decimal_places=0)
    action          = serializers.CharField()
    date_work            = serializers.DateTimeField()
    worked_hours    = serializers.FloatField(required=False, allow_null=True)
    statut_paiement = serializers.CharField(required=False, allow_null=True)


# ── SORTIE ────────────────────────────────────────────────────────────────────

class UpdateStatutOutputDTO(serializers.Serializer):
    """Réponse après mise à jour groupée de statut."""
    message = serializers.CharField()
    updated = serializers.IntegerField()
    ids     = serializers.ListField(child=serializers.IntegerField())


class CreateAttendanceOutputDTO(serializers.Serializer):
    """Réponse après création manuelle d'une attendance."""
    message           = serializers.CharField()
    id                = serializers.IntegerField()
    action            = serializers.CharField()
    statut_attendance = serializers.CharField()


class StatsOutputDTO(serializers.Serializer):
    """Compteurs globaux du dashboard."""
    nombre_employes         = serializers.IntegerField()
    somme_totale_en_attente = serializers.FloatField()
    somme_totale_impaye     = serializers.FloatField()


class HistoriqueJourPaiementOutputDTO(serializers.Serializer):
    """Une ligne d'historique groupée par jour de paiement."""
    date_paiement = serializers.DateField()
    total         = serializers.FloatField()
    count         = serializers.IntegerField()


class HistoriqueStatsOutputDTO(serializers.Serializer):
    """Stats calculées sur l'historique filtré (avant pagination)."""
    total    = serializers.FloatField()
    moyenne  = serializers.FloatField()
    count    = serializers.IntegerField()
    employes = serializers.IntegerField()


class HistoriqueLigneOutputDTO(serializers.Serializer):
    """Une ligne de l'historique paginé."""
    id                   = serializers.IntegerField()
    date_paiement        = serializers.DateField()
    nombre_jours         = serializers.IntegerField()
    montant_total        = serializers.FloatField()
    employe__nom_complet = serializers.CharField()
    employe__id          = serializers.IntegerField()
    employe__departement = serializers.CharField(allow_null=True)


class HistoriquePagineOutputDTO(serializers.Serializer):
    """Réponse complète de l'historique paginé."""
    results     = HistoriqueLigneOutputDTO(many=True)
    page        = serializers.IntegerField()
    page_size   = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    total_count = serializers.IntegerField()
    stats       = HistoriqueStatsOutputDTO()