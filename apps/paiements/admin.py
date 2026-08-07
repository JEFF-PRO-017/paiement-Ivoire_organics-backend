from django.contrib import admin
from .models import  Paiement

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display  = ('id','employe', 'date_paiement','montant', 'phone_number', 'methode_paiement', 'type_paiement',  'reference','date_envoi','date_confirmation', 'statut')
    list_filter   = ('statut', 'methode_paiement', 'type_paiement')
    search_fields = ('employe__nom_complet', 'reference')
