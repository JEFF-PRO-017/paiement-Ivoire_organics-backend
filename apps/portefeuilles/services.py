from django.utils import timezone

from apps.employes.models import Employe
from apps.odoo_attendance.models import Attendance
from .models import Portefeuille, HistoriquePaiement


# TODO A REVOIR
def confirmer_rh(portefeuille: Portefeuille) -> Portefeuille:
    portefeuille.statut = 'IMPAYE'
    portefeuille.save(update_fields=['statut', 'modifie_le'])
    return portefeuille


def marquer_paye(portefeuille: Portefeuille) -> Portefeuille:

    # Enregistrer dans l'historique
    HistoriquePaiement.objects.create(
        employe       = portefeuille.employe,
        portefeuille  = portefeuille,
        date_paiement = timezone.now().date(),
        montant_total = portefeuille.montant_total,
        nombre_jours  = portefeuille.nombre_jours_impayes,
        periodes_paiement = portefeuille.periodes_paiement,
        statut = 'PAYE',
    )
    portefeuille.statut = 'PAYE'
    portefeuille.save(update_fields=['modifie_le','statut'])
    return portefeuille
# ......................................................................

def update_statut_bulk(ids: list, statut_paiement: str = None, statut_attendance: str = None) -> dict:
        """
        Met à jour le statut de plusieurs Attendance en une seule requête.
        Retourne un dict avec le nombre de lignes modifiées.
        """
        if not ids:
            raise ValueError("La liste d'IDs est vide.")

        # Validation des valeurs
        statuts_paiement_valides   = ['EN_ATTENTE', 'PAYE', 'IMPAYE']
        statuts_attendance_valides = ['CREATION_AUTO', 'CREATION_MANUELLE', 'ARCHIVE']

        if statut_paiement and statut_paiement not in statuts_paiement_valides:
            raise ValueError(f"statut_paiement invalide : {statut_paiement}")

        if statut_attendance and statut_attendance not in statuts_attendance_valides:
            raise ValueError(f"statut_attendance invalide : {statut_attendance}")

        if not statut_paiement and not statut_attendance:
            raise ValueError("Au moins un statut doit être fourni.")

        # Construction du dict de mise à jour
        fields_to_update = {}
        if statut_paiement:
            fields_to_update['statut_paiement'] = statut_paiement
        if statut_attendance:
            fields_to_update['statut_attendance'] = statut_attendance

        qs = Attendance.objects.filter(id__in=ids)
        updated = qs.update(**fields_to_update)

        return {
            'updated': updated,
            'ids':     ids,
        }

def create_attendance_manuel(data: dict) -> Attendance:
    """
    Crée une attendance manuellement par l'admin.
    statut_attendance est forcé à CREATION_MANUELLE.
    """
    required_fields = ['employee_id', 'action', 'name']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Le champ '{field}' est obligatoire.")

    if data.get('action') not in ['sign_in', 'sign_out']:
        raise ValueError("action doit être 'sign_in' ou 'sign_out'.")

    return Attendance.objects.create(
        employee_id              = data['employee_id'],
        employee_name            = data.get('employee_name'),
        action                   = data['action'],
        name                     = data['name'],
        worked_hours             = data.get('worked_hours'),
        date_validation_paiement = data.get('date_validation_paiement'),
        statut_paiement          = data.get('statut_paiement', 'EN_ATTENTE'),
        statut_attendance        = 'CREATION_MANUELLE',  # ← forcé
    )


@staticmethod
def get_attendances_par_employe(statut_paiement=None, statut_attendance=None) -> list:
    """
    Retourne les attendances groupées par employé.
    """
    qs = Attendance.objects.all()

    if statut_paiement:
        qs = qs.filter(statut_paiement=statut_paiement)
    if statut_attendance:
        qs = qs.filter(statut_attendance=statut_attendance)

    # Grouper par employee_id
    grouped = {}
    for att in qs:
        if att.employee_id not in grouped:
            grouped[att.employee_id] = []
        grouped[att.employee_id].append(att)

    result = []
    for employee_id, attendances in grouped.items():
        try:
            employe = Employe.objects.get(odoo_id=employee_id)
        except Employe.DoesNotExist:
            employe = None

        result.append({
            'employe':        employe,
            'attendance_list': attendances,
        })

    return result


@staticmethod
def get_attendance_detail(pk: int) -> Attendance:
    try:
        return Attendance.objects.get(pk=pk)
    except Attendance.DoesNotExist:
        raise ValueError(f"Attendance {pk} introuvable.")