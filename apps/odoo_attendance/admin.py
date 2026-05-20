from django.contrib import admin
from django.utils.html import format_html
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    # ── Colonnes ──────────────────────────────────────────────────────────────
    list_display = (
        "oodo_attendance_id",
        "employee_name",
        "employee_id",
        "action_badge",
        "name",
        "worked_hours_display",
    )

    # ── Filtres latéraux ──────────────────────────────────────────────────────
    list_filter = ("action", "name")

    # ── Recherche ─────────────────────────────────────────────────────────────
    search_fields = ("employee_id", "employee_name", "oodo_attendance_id")

    # ── Tri par défaut ────────────────────────────────────────────────────────
    ordering = ("-name",)

    # ── Lecture seule (données Odoo — ne pas modifier manuellement) ───────────
    readonly_fields = (
        "oodo_attendance_id", "employee_id", "employee_name",
        "action", "name", "worked_hours",
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
        color = "green" if obj.worked_hours > 2 else "orange"
        return format_html(
            '<span style="color:{}">{:.2f} h</span>', color, obj.worked_hours
        )