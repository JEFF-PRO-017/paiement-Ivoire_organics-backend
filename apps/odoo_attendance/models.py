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
    

class Attendance(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('PAYE',       'Payé'),
        ('IMPAYE',     'Impayé'),
    ]

    STATUT_A = [
        ('CREATION_AUTO',     "Créé par le système"),
        ('CREATION_MANUELLE', "Créé par l'admin"),
        ('ARCHIVE',           "Supprimé par l'admin"),
    ]

    ACTION_CHOICES = [
        ('sign_in',  'Entrée'),
        ('sign_out', 'Sortie'),
    ]

    employe                  = models.ForeignKey(Employe, on_delete=models.PROTECT)
    action                   = models.CharField(max_length=10, choices=ACTION_CHOICES)
    date_work                = models.DateTimeField()                                        # timestamp de l'action
    worked_hours             = models.FloatField(null=True, blank=True)                      # durée du shift
    odoo_attendance_id       = models.CharField(max_length=50, unique=True, null=True, blank=True)
    date_validation_paiement = models.DateTimeField(null=True, blank=True)
    statut_paiement          = models.CharField(max_length=15, choices=STATUT_CHOICES, default='EN_ATTENTE')
    statut_attendance        = models.CharField(max_length=20, choices=STATUT_A, default='CREATION_AUTO')  # ← virgule supprimée
    montant_journalier       = models.DecimalField(max_digits=12, decimal_places=2)
    class Meta:
        db_table = 'odoo_attendance'

    def __str__(self):
        return f"Attendance {self.odoo_attendance_id} - {self.action} at {self.name}"
    



