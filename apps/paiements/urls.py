from django.urls import path

from .views import (
    AttendanceDetailView, AttendanceView, ExportPdfHistoriqueView,
    HistoriqueEmployeView, HistoriqueParJourPaiementView, HistoriqueView,
    JoursCumulesView, StatsView, UpdateStatutAttendanceView,
)

urlpatterns = [
    path('attendances/', AttendanceView.as_view(), name='attendance-list'),
    path('attendances/<int:pk>/', AttendanceDetailView.as_view(), name='attendance-detail'),
    # TODO:CONTINUER LA VERIFICATION A CE NIVEAU
    path('attendances/update-statut/', UpdateStatutAttendanceView.as_view(), name='attendance-update-statut'),

    path('employe/', HistoriqueEmployeView.as_view(), name='historique-employe'),

    path('historique/', HistoriqueView.as_view(), name='historique-list'),
    path('historique/par-jour/', HistoriqueParJourPaiementView.as_view(), name='historique-par-jour'),
    path('historique/export-pdf/', ExportPdfHistoriqueView.as_view(), name='historique-export-pdf'),

    path('stats/', StatsView.as_view(), name='stats'),
    path('jours-cumules/', JoursCumulesView.as_view(), name='jours-cumules'),
]