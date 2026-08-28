from django.contrib import admin
from django.utils.html import format_html
from .models import Attendance, Employe, Signalement, TarifJournalier
from django.utils import timezone

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('id','odoo_attendance_id', 'employe__nom_complet','employe__id', 'action','date', 'date_work', 'worked_hours', 'statut_paiement', 'statut_attendance','date_validation_paiement','montant_journalier')
    list_filter = ('statut_paiement', 'statut_attendance', 'montant_journalier')
    search_fields = ('odoo_attendance_id', 'employe__nom_complet')
    ordering = ('-date_work',)
    
@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display  = ('id','odoo_id', 'nom_complet', 'departement', 'site_travail','mobile_phone','operateur_mobile', 'clientReferenceId','statut','permanent')
    list_filter   = ('statut', 'departement','site_travail','operateur_mobile','permanent')
    search_fields = ('nom_complet', 'odoo_id')



@admin.register(TarifJournalier)
class TarifJournalierAdmin(admin.ModelAdmin):
    list_display = ('id','montant', 'date_effet', 'est_actif')
    list_filter = ('date_effet',)
    ordering = ('-date_effet',)
    search_fields = ('montant',)

    @admin.display(description="Tarif en vigueur", boolean=True)
    def est_actif(self, obj):
        """Coche le tarif actuellement en vigueur (visuel uniquement)."""
        dernier = (
            TarifJournalier.objects
            .filter(date_effet__lte=timezone.now().date())
            .order_by('-date_effet')
            .first()
        )
        return dernier and dernier.pk == obj.pk



@admin.register(Signalement)
class SignalementAdmin(admin.ModelAdmin):
    list_display  = ('employe__nom_complet', 'demandeur__email', 'type_demande', 'jour', 'raison','cree_le')
    list_filter   = ('type_demande', 'cree_le')
    search_fields = ('type_demande', 'jour')