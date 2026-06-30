from django.contrib import admin
from django.utils.html import format_html
from .models import Attendance, Employe


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    # ── Colonnes ──────────────────────────────────────────────────────────────
    list_display = (
        "odoo_attendance_id",
        "employe",
        "action_badge",
        "date_work",
        "worked_hours_display",
    )

    # ── Filtres latéraux ──────────────────────────────────────────────────────
    list_filter = ("action", "date_work")

    # ── Recherche ─────────────────────────────────────────────────────────────
    search_fields = ("employe", "odoo_attendance_id")

    # ── Tri par défaut ────────────────────────────────────────────────────────
    ordering = ("-date_work",)

    # ── Lecture seule (données Odoo — ne pas modifier manuellement) ───────────
    readonly_fields = (
        "odoo_attendance_id", "employe",
        "action", "date_work", "worked_hours",
    )

    # ── Pagination ────────────────────────────────────────────────────────────
    list_per_page = 50

    # ── Colonnes calculées ────────────────────────────────────────────────────

    @admin.display(description="Action")
    def action_badge(self, obj):
        color  = "green" if obj.action == "sign_in" else "crimson"
        label  = "🟢 Entrée" if obj.action == "sign_in" else "🔴 Sortie"
        return format_html(
            '<span style="color:{}; font-weight:bold">{}</span>', color, label
        )

    @admin.display(description="Heures travaillées", ordering="worked_hours")
    def worked_hours_display(self, obj):
        if obj.worked_hours is None:
            return format_html('<span style="color:gray">—</span>')
        color  = "green" if obj.worked_hours > 2 else "orange"
        heures = f"{obj.worked_hours:.2f} h"   # ← formaté en dehors
        return format_html(
            '<span style="color:{}">{}</span>', color, heures
        )

@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display  = ('odoo_id', 'nom_complet', 'departement', 'site_travail', 'statut')
    list_filter   = ('statut', 'departement')
    search_fields = ('nom_complet', 'odoo_id')