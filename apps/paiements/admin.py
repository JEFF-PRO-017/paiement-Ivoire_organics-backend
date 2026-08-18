from django.contrib import admin
from .models import  ConfigurationPaiement, Paiement

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display  = ('id','employe', 'date_paiement','montant', 'phone_number', 'methode_paiement', 'type_paiement',  'reference','date_envoi','date_confirmation', 'statut')
    list_filter   = ('statut', 'methode_paiement', 'type_paiement')
    search_fields = ('employe__nom_complet', 'reference')

@admin.register(ConfigurationPaiement)
class ConfigurationPaiementAdmin(admin.ModelAdmin):
    list_display = ('id','site','mode','date_changement_mode','derniere_execution_auto')
    list_filter = ('mode','date_changement_mode')
