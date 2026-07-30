import os
from django.conf import settings
from django.core.mail import EmailMessage

from apps.odoo_attendance.models import Signalement


def envoyer_mail_signalement(signalement: Signalement):
    titre = f"{signalement.get_type_demande_display()} — {signalement.employe.nom_complet}"
    corps = (
        f"Demandeur : {signalement.demandeur.email}\n"
        f"Employé concerné : {signalement.employe.nom_complet} (ID {signalement.employe.id})\n"
        f"Jour concerné : {signalement.jour}\n"
        f"Type de demande : {signalement.get_type_demande_display()}\n\n"
        f"Raison :\n{signalement.raison}\n"
    )

    EmailMessage(
        subject=titre,
        body=corps,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.MAINTENANCE_EMAIL],   # ⚠️ à définir dans .env
        reply_to=[signalement.demandeur.email],  # mail du user récupéré depuis request.user, jamais saisi
    ).send(fail_silently=False)