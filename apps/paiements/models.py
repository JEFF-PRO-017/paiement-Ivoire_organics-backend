import uuid
from django.db import models
from apps.odoo_attendance.models import Attendance, Employe
from phonenumber_field.modelfields import PhoneNumberField 
from django.utils import timezone
from datetime import timedelta



class Paiement(models.Model):
    STATUT_CHOICES = [
        ('PENDING', 'En attente'),
        ('SUCCESS', 'Payé'),
        ('FAILED', 'Echoué'),
    ]
    METHODE_CHOICES = [('ci.orange', 'Orange Money'), ('ci.mtn', 'MTN Money')]
    TYPE_CHOICES = [
        ('GROUPE', 'Paiement groupé'),
        ('AUTOMATIQUE', 'Paiement automatique'),
        ('DEMANDE', 'Paiement à la demande'),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.PROTECT, related_name='historique_paiements')
    date_paiement = models.DateField()
    attendances = models.ManyToManyField(Attendance, related_name='paiements')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, null=True, blank=True)

    montant = models.DecimalField(max_digits=12, decimal_places=2)
    phone_number = PhoneNumberField()
    methode_paiement = models.CharField(max_length=10, choices=METHODE_CHOICES)
    type_paiement = models.CharField(max_length=15, choices=TYPE_CHOICES, default='DEMANDE')

    # reference envoyée à NotchPay — unique obligatoire (idempotence)
    reference = models.CharField(max_length=100, unique=True, editable=False)
    transaction_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    code_retour = models.IntegerField(null=True, blank=True)
    frais = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    message_erreur = models.TextField(null=True, blank=True)
    reponse_brute = models.JSONField(null=True, blank=True)

    date_envoi = models.DateTimeField(null=True, blank=True)
    date_confirmation = models.DateTimeField(null=True, blank=True)
    nombre_tentatives = models.PositiveSmallIntegerField(default=0)

    # Paiement : ajout
    bulk_transfer_id = models.CharField(max_length=50, null=True, blank=True)
    # Regroupe les paiements envoyés dans le même lot (utile pour retrouver/poller un lot entier)
    class Meta:
        db_table = 'paiements'
        ordering = ['-date_paiement']

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Paiement {self.date_paiement} — {self.employe.nom_complet}'


class ConfigurationPaiement(models.Model):
    MODE_CHOICES = [('MANUEL', 'Manuel'), ('AUTOMATIQUE', 'Automatique')]
    PERIODE_JOURS = 15

    mode = models.CharField(max_length=15, choices=MODE_CHOICES, default='MANUEL')
    date_changement_mode = models.DateTimeField(null=True, blank=True)
    derniere_execution_auto = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'configuration_paiement'

    @classmethod
    def get_instance(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def passer_en_automatique(self):
        self.mode = 'AUTOMATIQUE'
        self.date_changement_mode = timezone.now()
        self.derniere_execution_auto = None
        self.save()

    def passer_en_manuel(self):
        self.mode = 'MANUEL'
        self.save()

    def _date_reference(self):
        return self.derniere_execution_auto or self.date_changement_mode

    def echeance_atteinte(self):
        base = self._date_reference()
        if not base:
            return False
        return timezone.now() >= base + timedelta(days=self.PERIODE_JOURS)

    def jours_restants(self):
        if self.mode != 'AUTOMATIQUE':
            return None
        base = self._date_reference()
        if not base:
            return self.PERIODE_JOURS
        delta = (base + timedelta(days=self.PERIODE_JOURS)) - timezone.now()
        return max(delta.days, 0)