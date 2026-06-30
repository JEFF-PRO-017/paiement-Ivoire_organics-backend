from apps.odoo_attendance.models import Attendance, Employe
from .models import  HistoriquePaiement
from django.db.models import Sum, Avg, Count
from apps.odoo_attendance.models import Attendance, Employe



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
    required_fields = ['employee_id', 'action', 'date_work']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Le champ '{field}' est obligatoire.")

    if data.get('action') not in ['sign_in', 'sign_out']:
        raise ValueError("action doit être 'sign_in' ou 'sign_out'.")

    return Attendance.objects.create(
        employee_id              = data['employee_id'],
        action                   = data['action'],
        date_work                     = data['date_work'],
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
    qs = Attendance.objects.select_related('employe').all()

    if statut_paiement:
        qs = qs.filter(statut_paiement=statut_paiement)
    if statut_attendance:
        qs = qs.filter(statut_attendance=statut_attendance)

    # Grouper par employé (FK directe, plus de requête supplémentaire grâce au select_related)
    grouped = {}
    for att in qs:
        grouped.setdefault(att.employe_id, {'employe': att.employe, 'attendance_list': []})
        grouped[att.employe_id]['attendance_list'].append(att)

    return list(grouped.values())


@staticmethod
def get_attendance_detail(pk: int) -> Attendance:
    try:
        return Attendance.objects.get(pk=pk)
    except Attendance.DoesNotExist:
        raise ValueError(f"Attendance {pk} introuvable.")
    

def appliquer_filtres_historique(request):
    """Construit le queryset d'historique de paiement selon les filtres en query params."""
    qs = (
        HistoriquePaiement.objects
        .select_related('employe')
        .order_by('-date_paiement')
    )
    if search := request.query_params.get('search'):
        qs = qs.filter(employe__nom_complet__icontains=search)

    dept = request.query_params.get('dept')
    if dept and dept != 'Tous':
        qs = qs.filter(employe__departement=dept)

    if date_debut := request.query_params.get('date_debut'):
        qs = qs.filter(date_paiement__gte=date_debut)

    if date_fin := request.query_params.get('date_fin'):
        qs = qs.filter(date_paiement__lte=date_fin)

    return qs


def get_historique_employe(employe_id):
    """Retourne le queryset d'historique de paiement d'un employé donné."""
    return HistoriquePaiement.objects.filter(employe_id=employe_id)


def get_stats_globales():
    """Calcule les compteurs globaux du dashboard."""
    nombre_employes = Employe.objects.filter(statut='ACTIF').count()

    attentes = Attendance.objects.filter(statut_paiement__in=['EN_ATTENTE', 'IMPAYE'])
    impayes  = Attendance.objects.filter(statut_paiement='IMPAYE')

    somme_attente = attentes.aggregate(total=Sum('montant_journalier'))['total'] or 0
    somme_impaye  = impayes.aggregate(total=Sum('montant_journalier'))['total'] or 0

    return {
        'nombre_employes':         nombre_employes,
        'somme_totale_en_attente': somme_attente,
        'somme_totale_impaye':     somme_impaye,
    }


def get_jours_cumules_impayes():
    """Retourne la liste triée des dates distinctes d'attendances impayées."""
    dates = Attendance.objects.filter(statut_paiement='IMPAYE').values_list('date_work', flat=True)
    return sorted(set(dates))


def get_historique_stats(qs):
    """Calcule les stats agrégées sur un queryset d'historique (avant pagination)."""
    stats_qs = qs.aggregate(
        total   = Sum('montant_total'),
        moyenne = Avg('montant_total'),
        count   = Count('id'),
    )
    nb_employes = qs.values('employe_id').distinct().count()

    return {
        'total':    stats_qs['total']   or 0,
        'moyenne':  round(stats_qs['moyenne'] or 0),
        'count':    stats_qs['count']   or 0,
        'employes': nb_employes,
    }


def get_historique_par_jour(qs, limit):
    """Regroupe un queryset d'historique par date de paiement."""
    return (
        qs.values('date_paiement')[:limit]
        .annotate(total=Sum('montant_total'), count=Count('id'))
    )