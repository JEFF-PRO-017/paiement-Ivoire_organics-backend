from django.contrib import admin
from .models import Employe

@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display  = ('odoo_id', 'nom_complet', 'departement', 'site_travail', 'statut')
    list_filter   = ('statut', 'departement')
    search_fields = ('nom_complet', 'odoo_id')
