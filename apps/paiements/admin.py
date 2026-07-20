from django.contrib import admin
from .models import  Paiement

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display  = ('employe', 'date_paiement')
    search_fields = ('employe__nom_complet',)
