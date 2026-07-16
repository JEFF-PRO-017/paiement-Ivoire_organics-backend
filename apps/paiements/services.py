from apps.odoo_attendance.models import Attendance, Employe
from apps.odoo_attendance.services import get_montant_journalier
from .models import  HistoriquePaiement
from django.db.models import Sum, Avg, Count
from apps.odoo_attendance.models import Attendance, Employe

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError as DRFValidationError

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
    
    employee_id = data['employee_id']
    employe = Employe.objects.filter(id=employee_id).first()
    if not employe:
        raise ValueError("cet employe n'existe pas")

    attendance = Attendance(
        employe                  = employe,
        action                   = data['action'],
        date_work                     = data['date_work'],
        worked_hours             = data.get('worked_hours'),
        date_validation_paiement = data.get('date_validation_paiement'),
        statut_paiement          = data.get('statut_paiement', 'EN_ATTENTE'),
        statut_attendance        = 'CREATION_MANUELLE',  # ← forcé
        montant_journalier       = get_montant_journalier(data['date_work'].date())
    )
    try:
        attendance.full_clean()
        attendance.save()
    except DjangoValidationError as e:
        raise DRFValidationError(e.message_dict if hasattr(e, "message_dict") else e.messages)
    except IntegrityError:
        # Filet de sécurité si jamais une race condition contourne full_clean()
        raise DRFValidationError({
            "code": "attendance_deja_existante",
            "detail": "Cet employé a déjà une attendance enregistrée pour cette date."
        })
    return attendance

@staticmethod
def get_attendances_par_employe(qs,statut_paiement=None, statut_attendance=None) -> list:
    """
    Retourne les attendances groupées par employé.
    """
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


def get_attendance_detail(pk: int, site: str = None) -> Attendance:
    """Récupère une attendance par son id, en vérifiant qu'elle appartient bien au site demandé."""
    try:
        attendance = Attendance.objects.select_related('employe').get(pk=pk)
    except Attendance.DoesNotExist:
        raise ValueError(f"Attendance {pk} introuvable.")

    if site and attendance.employe.site_travail != site:
        raise ValueError(f"Attendance {pk} introuvable.")  # on cache l'existence plutôt qu'un 403

    return attendance


def appliquer_filtres_historique(request, site: str = None):
    """Construit le queryset d'historique de paiement selon les filtres en query params + le site."""
    qs = (
        HistoriquePaiement.objects
        .select_related('employe')
        .order_by('-date_paiement')
    )
    if site:
        qs = qs.filter(employe__site_travail=site)

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


def get_stats_globales(qs):
    """
    Calcule les compteurs globaux du dashboard.
    qs : queryset Attendance déjà filtré par site (et autres filtres éventuels).
    """
    nombre_employes = Employe.objects.filter(statut='ACTIF', site_travail__in=qs.values('employe__site_travail')).distinct().count()

    attentes = qs.filter(statut_paiement='EN_ATTENTE')
    impayes  = qs.filter(statut_paiement='IMPAYE')

    somme_attente = attentes.aggregate(total=Sum('montant_journalier'))['total'] or 0
    somme_impaye  = impayes.aggregate(total=Sum('montant_journalier'))['total'] or 0

    return {
        'nombre_employes':         nombre_employes,
        'somme_totale_en_attente': somme_attente,
        'somme_totale_impaye':     somme_impaye,
    }


def get_jours_cumules_impayes(site: str = None):
    """Retourne la liste triée des dates distinctes d'attendances impayées, filtrée par site."""
    qs = Attendance.objects.filter(statut_paiement='IMPAYE')
    if site:
        qs = qs.filter(employe__site_travail=site)

    dates = qs.values_list('date_work', flat=True)
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

def get_historique_employe(employe_id):
    """Retourne le queryset d'historique de paiement d'un employé donné."""
    return HistoriquePaiement.objects.filter(employe_id=employe_id)