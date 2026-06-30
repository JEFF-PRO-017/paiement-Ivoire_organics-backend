from django.urls import path
from .views import (
    HistoriqueEmployeView, UpdateStatutAttendanceView, CreateAttendanceManuelView,
    AttendanceListView, AttendanceDetailView, StatsView, JoursCumulesView,
    HistoriqueView, HistoriqueParJourPaiementView, ExportPdfHistoriqueView,
)

urlpatterns = [
    path('historique/employe/',        HistoriqueEmployeView.as_view(),         name='historique-employe'),
    path('attendances/update-statut/', UpdateStatutAttendanceView.as_view(),    name='attendance-update-statut'),
    path('attendances/creer-manuel/',  CreateAttendanceManuelView.as_view(),    name='attendance-creer-manuel'),
    path('attendances/',               AttendanceListView.as_view(),            name='attendance-list'),
    path('attendances/<int:pk>/',      AttendanceDetailView.as_view(),          name='attendance-detail'),
    path('stats/',                     StatsView.as_view(),                     name='stats'),
    path('jours-cumules/',             JoursCumulesView.as_view(),              name='jours-cumules'),
    path('historique/',                HistoriqueView.as_view(),                name='historique'),
    path('historique/par-jour/',       HistoriqueParJourPaiementView.as_view(), name='historique-par-jour'),
    path('historique/export-pdf/',     ExportPdfHistoriqueView.as_view(),       name='historique-export-pdf'),
]