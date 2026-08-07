import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from apps.odoo_attendance.models import Attendance, Employe


class Paiement(models.Model):
    STATUT_CHOICES = [
        # ('PENDING', 'En attente'),
        ('ENCOURS', 'En cours'),
        ('SUCCESS', 'Payé'),
        ('FAILED', 'Echoué'),
    ]
    METHODE_CHOICES = [('ORANGE_CIV', 'Orange Money'), ('MTN_MOMO_CIV', 'MTN Money')]
    TYPE_CHOICES = [
        ('GROUPE', 'Paiement groupé'),
        ('AUTOMATIQUE', 'Paiement automatique'),
        ('DEMANDE', 'Paiement à la demande'),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.PROTECT, related_name='historique_paiements')
    date_paiement = models.DateField()
    attendances = models.ManyToManyField(Attendance, related_name='paiements')
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='PENDING')

    montant = models.DecimalField(max_digits=12, decimal_places=2)
    phone_number = PhoneNumberField()
    methode_paiement = models.CharField(max_length=15, choices=METHODE_CHOICES)
    type_paiement = models.CharField(max_length=15, choices=TYPE_CHOICES, default='DEMANDE')

    # reference envoyée à PawaPay comme "payoutId" -> sert aussi d'identifiant unique (idempotence)
    reference = models.CharField(max_length=100, unique=True, editable=False)
    reponse_brute = models.JSONField(null=True, blank=True)

    date_envoi = models.DateTimeField(null=True, blank=True)
    date_confirmation = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'paiements'
        ordering = ['-date_paiement']

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = str(uuid.uuid4())  # PawaPay exige un UUID pour payoutId
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Paiement {self.date_paiement} — {self.employe.nom_complet}'

    def mettre_a_jour_statut(self, nouveau_statut):
        """
        Point UNIQUE de mise à jour du statut du paiement.
        Répercute automatiquement le changement sur les attendances liées.
        """
        self.statut = nouveau_statut
        self.date_confirmation = timezone.now()
        self.save()

        if nouveau_statut == 'SUCCESS':
            self.attendances.update(statut_paiement='PAYE', date_validation_paiement=timezone.now())
        if nouveau_statut == 'ENCOURS':
            self.attendances.update(statut_paiement='ENCOURS', date_validation_paiement=timezone.now())
        elif nouveau_statut == 'FAILED':
            self.attendances.update(statut_paiement='IMPAYE')


class ConfigurationPaiement(models.Model):
    MODE_CHOICES = [('MANUEL', 'Manuel'), ('AUTOMATIQUE', 'Automatique')]

    mode = models.CharField(max_length=15, choices=MODE_CHOICES, default='MANUEL')
    date_changement_mode = models.DateTimeField(null=True, blank=True)
    derniere_execution_auto = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'configuration_paiement'

    @classmethod
    def get_instance(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def periode_jours(self):
        """Durée du cycle automatique, configurable via .env (PAWAPAY_PERIODE_JOURS)."""
        return settings.PAWAPAY_PERIODE_JOURS

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
        return timezone.now() >= base + timedelta(days=self.periode_jours)

    def jours_restants(self):
        if self.mode != 'AUTOMATIQUE':
            return None
        base = self._date_reference()
        if not base:
            return self.periode_jours
        delta = (base + timedelta(days=self.periode_jours)) - timezone.now()
        return max(delta.days, 0)