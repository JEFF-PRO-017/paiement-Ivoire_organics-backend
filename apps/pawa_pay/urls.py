from django.urls import path
from .views import ConfigurationPaiementView, PaiementManuelView, SoldePawaPayView

urlpatterns = [
    path('config-paiement/', ConfigurationPaiementView.as_view()),
    path('paiement-manuel/', PaiementManuelView.as_view()),
    path('solde-pawapay/', SoldePawaPayView.as_view()),
]