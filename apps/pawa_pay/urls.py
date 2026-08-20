from django.urls import path
from .views import ConfigurationPaiementView, PaiementManuelView, SoldePawaPayView, VerifierPaiementsEnCoursView

urlpatterns = [
    path('config_paiement/', ConfigurationPaiementView.as_view()),
    path('paiement_manuel/', PaiementManuelView.as_view()),
    path('solde_pawapay/', SoldePawaPayView.as_view()),
    path('verifier_en_cours/', VerifierPaiementsEnCoursView.as_view(), name='verifier_paiements_en_cours'),
]