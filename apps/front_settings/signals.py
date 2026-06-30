from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import CustomUser
from .services import ParametreService


@receiver(post_save, sender=CustomUser)
def creer_parametre_a_la_creation_du_user(sender, instance, created, **kwargs):
    """Un seul Parametre créé une fois, à la création du compte."""
    if created:
        ParametreService.get_ou_creer(instance)