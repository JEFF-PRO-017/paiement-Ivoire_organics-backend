from django.urls import path
from .views import ConfigurationPaiementView, PaiementManuelView, RelancePaiementEchoueView, SoldeNotchPayView
from .webhook import notchpay_webhook

urlpatterns = [
    path('config-paiement/', ConfigurationPaiementView.as_view()),
    path('paiement-manuel/', PaiementManuelView.as_view()),
    path('paiement-relance/', RelancePaiementEchoueView.as_view()),
    path('webhook/notchpay/', notchpay_webhook),
    path('solde-notchpay/', SoldeNotchPayView.as_view()),
]