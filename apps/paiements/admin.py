from django.contrib import admin
from .models import HistoriquePaiement

@admin.register(HistoriquePaiement)
class HistoriquePaiementAdmin(admin.ModelAdmin):
    list_display  = ('employe', 'date_paiement', 'montant_total', 'nombre_jours')
    search_fields = ('employe__nom_complet',)
