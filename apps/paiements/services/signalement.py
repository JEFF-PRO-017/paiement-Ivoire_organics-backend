from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.odoo_attendance.models import Attendance, Employe, Signalement
from apps.paiements.services.services import create_attendance_manuel
from .mailer import envoyer_mail_signalement


@transaction.atomic
def create_signalement(*, employe_id: int, type_demande: str, jour, raison: str, demandeur) -> Signalement:
    employe = get_object_or_404(Employe, pk=employe_id)
    attendance = None

    if type_demande == 'CREATION':
        # réutilise la fonction existante : gère validation, unicité, calcul du montant_journalier
        # statut_attendance='CREATION_MANUELLE' et statut_paiement='EN_COURS_TRAITEMENT' sont déjà forcés dedans
        attendance = create_attendance_manuel({
            'employe_id': employe_id,
            'action': 'sign_out',                    # ⚠️ valeur par défaut, à ajuster si besoin
            'date_work': f"{jour}T08:00:00Z",         # ⚠️ heure par défaut
            'worked_hours': None, 
            'statut_paiement':'EN_COURS_TRAITEMENT_CREATION'                   # ⚠️ renseigné lors du traitement réel par la maintenance
        })

    elif type_demande == 'SUPPRESSION':
        # une attendance existe déjà ce jour → on la flag, pas de création (contrainte unique_employe_par_jour)
        attendance = Attendance.objects.filter(employe=employe, date=jour).first()
        if attendance:
            attendance.statut_paiement = 'EN_COURS_TRAITEMENT_SUPPRESION'
            attendance.save(update_fields=['statut_paiement'])

    signalement = Signalement.objects.create(
        employe=employe,
        demandeur=demandeur,
        type_demande=type_demande,
        jour=jour,
        raison=raison,
        attendance=attendance,
    )

    # envoyer_mail_signalement(signalement)
    return signalement