from django.db import models
from phonenumber_field.modelfields import PhoneNumberField 


class Employe(models.Model):
    STATUT_CHOICES = [('ACTIF', 'Actif'), ('INACTIF', 'Inactif')]

    odoo_id        = models.CharField(max_length=20, unique=True)
    nom_complet    = models.CharField(max_length=150)
    departement    = models.CharField(max_length=100)
    site_travail   = models.CharField(max_length=100)
    statut         = models.CharField(max_length=10, choices=STATUT_CHOICES, default='INACTIF')
    # Empreinte digitale (template binaire — rempli par le driver USB)
    empreinte_template = models.BinaryField(null=True, blank=True)
    mobile_phone = PhoneNumberField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.phone and not str(self.phone).startswith('+'):
            self.phone = None
        super().save(*args, **kwargs)
    class Meta:
        db_table = 'employes'

    def __str__(self):
        return f'{self.nom_complet} ({self.odoo_id})'
