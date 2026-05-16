from django.urls import path
from .views import stats_view, jours_cumules_view, historique_view, export_pdf_historique_view

urlpatterns = [
    path('stats/',                   stats_view,                  name='dashboard-stats'),
    path('jours-cumules/',           jours_cumules_view,          name='dashboard-jours'),
    path('historique/',              historique_view,             name='dashboard-historique'),
    path('historique/export-pdf/',   export_pdf_historique_view,  name='dashboard-export-pdf'),
]