from django.db import models


class Employe(models.Model):
    STATUT_CHOICES = [('ACTIF', 'Actif'), ('INACTIF', 'Inactif')]

    odoo_id        = models.CharField(max_length=20, unique=True)
    nom_complet    = models.CharField(max_length=150)
    departement    = models.CharField(max_length=100)
    site_travail   = models.CharField(max_length=100)
    statut         = models.CharField(max_length=10, choices=STATUT_CHOICES, default='ACTIF')
    # Empreinte digitale (template binaire — rempli par le driver USB)
    empreinte_template = models.BinaryField(null=True, blank=True)

    class Meta:
        db_table = 'employes'

    def __str__(self):
        return f'{self.nom_complet} ({self.odoo_id})'
