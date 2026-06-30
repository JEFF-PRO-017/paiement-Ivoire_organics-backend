from django.db import models
from apps.odoo_attendance.models import Employe


class HistoriquePaiement(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE',   'En attente'),
        ('PAYE',         'Payé'),
        ('IMPAYE',       'Impayé'),
    ]
    employe       = models.ForeignKey(Employe, on_delete=models.PROTECT, related_name='historique_paiements')
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
