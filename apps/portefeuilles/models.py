from django.db import models
from apps.employes.models import Employe


class Portefeuille(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE',   'En attente'),
        # ('CONFIRME_RH',  'Confirmé RH'),
        ('PAYE',         'Payé'),
        ('IMPAYE',       'Impayé'),
    ]

    employe             = models.ForeignKey(Employe, on_delete=models.PROTECT, related_name='portefeuilles')
    nombre_jours_impayes = models.PositiveIntegerField(default=0)
    montant_journalier  = models.DecimalField(max_digits=12, decimal_places=2)
    periodes_paiement   = models.JSONField(default=list)   # liste de dates ISO
    statut              = models.CharField(max_length=15, choices=STATUT_CHOICES, default='EN_ATTENTE')
    cree_le             = models.DateTimeField(auto_now_add=True)
    modifie_le          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'portefeuilles'
        ordering = ['-cree_le']

    @property
    def montant_total(self):
        return self.nombre_jours_impayes * self.montant_journalier

    def __str__(self):
        return f'Portefeuille #{self.id} — {self.employe.nom_complet}'


class HistoriquePaiement(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE',   'En attente'),
        ('PAYE',         'Payé'),
        ('IMPAYE',       'Impayé'),
    ]
    employe       = models.ForeignKey(Employe, on_delete=models.PROTECT, related_name='historique_paiements')
    portefeuille  = models.ForeignKey(Portefeuille, on_delete=models.SET_NULL, null=True, blank=True)
    date_paiement = models.DateField()
    montant_total = models.DecimalField(max_digits=12, decimal_places=2)
    nombre_jours  = models.PositiveIntegerField()
    periodes_paiement   = models.JSONField(default=list)
    statut              = models.CharField(max_length=15, choices=STATUT_CHOICES,null=True, blank=True)
    class Meta:
        db_table = 'historique_paiements'
        ordering = ['-date_paiement']

    def __str__(self):
        return f'Paiement {self.date_paiement} — {self.employe.nom_complet}'
