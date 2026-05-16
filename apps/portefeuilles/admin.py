from django.contrib import admin
from .models import Portefeuille, HistoriquePaiement

@admin.register(Portefeuille)
class PortefeuilleAdmin(admin.ModelAdmin):
    list_display  = ('id', 'employe', 'statut', 'nombre_jours_impayes', 'montant_journalier', 'cree_le')
    list_filter   = ('statut',)
    search_fields = ('employe__nom_complet', 'employe__odoo_id')

@admin.register(HistoriquePaiement)
class HistoriquePaiementAdmin(admin.ModelAdmin):
    list_display  = ('employe', 'date_paiement', 'montant_total', 'nombre_jours')
    search_fields = ('employe__nom_complet',)
