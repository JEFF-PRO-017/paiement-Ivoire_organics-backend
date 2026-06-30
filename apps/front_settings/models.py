from django.db import models
from django.conf import settings


class Parametre(models.Model):
    """
    Préférences d'affichage front — UNE seule ligne par utilisateur,
    quel que soit le nombre de sites auxquels il a accès.
    Le champ `site` est juste le site actif/courant, modifiable via PATCH.
    """

    MODE_CHOICES = [
        ('SOMBRE', 'Sombre'),
        ('CLAIR', 'Clair'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='parametre',
    )
    site = models.CharField(max_length=150, blank=True, default='')

    zoom = models.BooleanField(default=False)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='CLAIR')

    dashboard_composant_1 = models.BooleanField(default=True)
    dashboard_composant_2 = models.BooleanField(default=True)
    dashboard_composant_3 = models.BooleanField(default=True)
    dashboard_composant_4 = models.BooleanField(default=True)

    detail_composant_1 = models.BooleanField(default=True)
    detail_composant_2 = models.BooleanField(default=True)
    detail_composant_3 = models.BooleanField(default=True)
    detail_composant_4 = models.BooleanField(default=True)

    historique_composant_1 = models.BooleanField(default=True)
    historique_composant_2 = models.BooleanField(default=True)
    historique_composant_3 = models.BooleanField(default=True)

    class Meta:
        db_table = 'parametres'

    def __str__(self):
        return f'Paramètres {self.user.email}'

    def to_dict(self) -> dict:
        return {
            'zoom': self.zoom,
            'mode': self.mode,
            'site': self.site,
            'page_dashboard': {
                'composant_1': self.dashboard_composant_1,
                'composant_2': self.dashboard_composant_2,
                'composant_3': self.dashboard_composant_3,
                'composant_4': self.dashboard_composant_4,
            },
            'page_detail': {
                'composant_1': self.detail_composant_1,
                'composant_2': self.detail_composant_2,
                'composant_3': self.detail_composant_3,
                'composant_4': self.detail_composant_4,
            },
            'page_historique': {
                'composant_1': self.historique_composant_1,
                'composant_2': self.historique_composant_2,
                'composant_3': self.historique_composant_3,
            },
        }