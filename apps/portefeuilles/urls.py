from django.urls import path
from .views import (
    PortefeuilleListView, PortefeuilleDetailView,
    confirmer_rh_view, payer_view,
    historique_employe_view, export_pdf_view,
)

urlpatterns = [
    path('',                          PortefeuilleListView.as_view(),   name='portefeuille-list'),
    path('<int:pk>/',                 PortefeuilleDetailView.as_view(), name='portefeuille-detail'),
    path('<int:pk>/confirmer-rh/',    confirmer_rh_view,                name='confirmer-rh'),
    path('<int:pk>/payer/',           payer_view,                       name='payer'),
    path('<int:pk>/export-pdf/',      export_pdf_view,                  name='export-pdf'),
    path('historique/',               historique_employe_view,          name='historique-employe'),
]
