from django.db import models


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

    employee_id              = models.CharField(max_length=20)
    employee_name            = models.CharField(max_length=150, null=True, blank=True)
    action                   = models.CharField(max_length=10, choices=ACTION_CHOICES)
    name                     = models.DateTimeField()                                        # timestamp de l'action
    worked_hours             = models.FloatField(null=True, blank=True)                      # durée du shift
    odoo_attendance_id       = models.CharField(max_length=50, unique=True, null=True, blank=True)
    date_validation_paiement = models.DateTimeField(null=True, blank=True)
    statut_paiement          = models.CharField(max_length=15, choices=STATUT_CHOICES, default='EN_ATTENTE')
    statut_attendance        = models.CharField(max_length=20, choices=STATUT_A, default='CREATION_AUTO')  # ← virgule supprimée

    class Meta:
        db_table = 'odoo_attendance'

    def __str__(self):
        return f"Attendance {self.employee_id} - {self.action} at {self.name}"