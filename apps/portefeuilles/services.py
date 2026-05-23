from django.utils import timezone
from .models import Portefeuille, HistoriquePaiement


def confirmer_rh(portefeuille: Portefeuille) -> Portefeuille:
    portefeuille.statut = 'IMPAYE'
    portefeuille.save(update_fields=['statut', 'modifie_le'])
    return portefeuille


def marquer_paye(portefeuille: Portefeuille) -> Portefeuille:

    # Enregistrer dans l'historique
    HistoriquePaiement.objects.create(
        employe       = portefeuille.employe,
        portefeuille  = portefeuille,
        date_paiement = timezone.now().date(),
        montant_total = portefeuille.montant_total,
        nombre_jours  = portefeuille.nombre_jours_impayes,
        periodes_paiement = portefeuille.periodes_paiement,
        statut = 'PAYE',
    )
    portefeuille.statut = 'PAYE'
    portefeuille.save(update_fields=['modifie_le','statut'])
    return portefeuille
