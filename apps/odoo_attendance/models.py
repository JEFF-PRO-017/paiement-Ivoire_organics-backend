from django.db import models
from phonenumber_field.modelfields import PhoneNumberField 
from django.conf import settings


class Employe(models.Model):
    STATUT_CHOICES = [('ACTIF', 'Actif'), ('INACTIF', 'Inactif')]
    OPERATEUR_CHOICES = [('ORANGE_CIV', 'Orange Money'), ('MTN_MOMO_CIV', 'MTN Money')]

    odoo_id = models.CharField(max_length=20, unique=True)
    nom_complet = models.CharField(max_length=150)
    departement = models.CharField(max_length=100)
    site_travail = models.CharField(max_length=100)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='INACTIF')
    mobile_phone = PhoneNumberField(null=True, blank=True)
    # Déduit automatiquement du mobile_phone au save() — jamais saisi manuellement
    operateur_mobile = models.CharField(max_length=30, choices=OPERATEUR_CHOICES, null=True, blank=True)
    clientReferenceId = models.CharField(max_length=50, null=True, blank=True, unique=True)
    permanent = models.BooleanField(default=False)

    class Meta:
        db_table = 'employes'

    def save(self, *args, **kwargs):
        if self.mobile_phone and not str(self.mobile_phone).startswith('+'):
            self.mobile_phone = None

        if self.mobile_phone:
            numero = str(self.mobile_phone).replace('+225', '').replace(' ', '')
            if numero.startswith(('07', '08', '09')):
                self.operateur_mobile = 'ORANGE_CIV'
            elif numero.startswith(('05', '06', '04')):
                self.operateur_mobile = 'MTN_MOMO_CIV'
            else:
                self.operateur_mobile = None
        else:
            self.operateur_mobile = None

        # crée le clientReferenceId si il n'existe pas
        if not self.clientReferenceId:
            self.clientReferenceId = f"{self.odoo_id}-{self.nom_complet.replace(' ', '')}"

        if self.permanent :
            self.statut ='INACTIF'

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nom_complet} ({self.odoo_id})'


class Attendance(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),# avant validation par la rh
        ('PAYE', 'Payé'), # deja ok
        ('IMPAYE', 'Impayé'), # avant l'envoie a l'aggreateur
        ('EN_COURS','En cours'), # avant validation  de l'aggregateur
        ('EN_COURS_TRAITEMENT_SUPPRESION', "En cours de traitement (signalement SUPPRESION)"),
        ('EN_COURS_TRAITEMENT_CREATION', "En cours de traitement (signalement CREATION)"),
        ('ARCHIVE', "Supprimé par l'admin"),
    ]
    STATUT_A = [
        ('CREATION_AUTO', "Créé par le système"),
        ('CREATION_MANUELLE', "Créé par l'admin"),
    ]
    ACTION_CHOICES = [('sign_in', 'Entrée'), ('sign_out', 'Sortie')]

    employe = models.ForeignKey(Employe, on_delete=models.PROTECT)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES,default='sign_out')
    date_work = models.DateTimeField()
    date = models.DateField(editable=False)
    worked_hours = models.FloatField(null=True, blank=True)
    odoo_attendance_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    date_validation_paiement = models.DateTimeField(null=True, blank=True)
    statut_paiement = models.CharField(max_length=50, choices=STATUT_CHOICES, default='EN_ATTENTE')
    statut_attendance = models.CharField(max_length=20, choices=STATUT_A, default='CREATION_AUTO')
    montant_journalier = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'odoo_attendance'
        constraints = [
            models.UniqueConstraint(
                fields=['employe', 'date'],
                name='unique_employe_par_jour',
                violation_error_message="Cet employé a déjà une attendance enregistrée pour cette date.",
                violation_error_code='attendance_deja_existante',
            )
        ]

    def save(self, *args, **kwargs):
        if self.date_work:
            self.date = self.date_work.date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Attendance {self.odoo_attendance_id} - {self.action} at {self.date_work}"



class TarifJournalier(models.Model):
    montant  = models.DecimalField(max_digits=12, decimal_places=2,default=3000.0)

    #date a partir de quel le montant s'applique
    date_effet = models.DateField(unique=True)

    class Meta:
        db_table = 'tarif_journaliers'
        ordering = ['-date_effet']
        verbose_name = "Tarif Journalier"
        verbose_name_plural = "Tarif Journaliers"

    def __str__(self):
        return f"Tarif Journalier: {self.montant} à partir de {self.date_effet}"



class Signalement(models.Model):
    TYPE_CHOICES = [
        ('CREATION', 'Demande de création de présence'),
        ('SUPPRESSION', 'Demande de suppression de présence'),
    ]

    employe      = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='signalements')
    demandeur    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='signalements_envoyes')
    type_demande = models.CharField(max_length=15, choices=TYPE_CHOICES)
    jour         = models.DateField()
    raison       = models.TextField()
    cree_le      = models.DateTimeField(auto_now_add=True)
    attendance   = models.ForeignKey(Attendance, on_delete=models.SET_NULL, null=True, blank=True, related_name='signalements')  # ← ajouté : trace l'attendance impactée

    class Meta:
        db_table = 'signalements_attendance'
        ordering = ['-cree_le']

    def __str__(self):
        return f"{self.get_type_demande_display()} · {self.employe} · {self.jour}"  # virgule en trop retirée



