from django.http import HttpResponse

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.paiements.pdf import generer_pdf_historique
from utils.pagination import StandardPagination

from .dto import (
    UpdateStatutInputDTO, UpdateStatutOutputDTO,
    CreateAttendanceManuelInputDTO, CreateAttendanceOutputDTO,
    StatsOutputDTO,
)
from .serializers import (
    AttendanceSerializer, AttendanceParEmployeSerializer, HistoriquePaiementSerializer,
)
from .services import (
    get_attendance_detail, get_attendances_par_employe,
    update_statut_bulk, create_attendance_manuel,
    appliquer_filtres_historique, get_historique_employe,
    get_stats_globales, get_jours_cumules_impayes,
    get_historique_stats, get_historique_par_jour,
)

# IsAuthenticated est déjà la permission par défaut (voir settings.py REST_FRAMEWORK).


# ── Helper interne : pagine un queryset/liste avec StandardPagination ───────

def _paginate(request, queryset, serializer_class):
    """
    Pagine un queryset (ou une liste) avec StandardPagination et le sérialise.
    Retourne directement une Response prête à renvoyer.
    """
    paginator = StandardPagination()
    page      = paginator.paginate_queryset(queryset, request)
    data      = serializer_class(page, many=True).data
    return paginator.get_paginated_response(data)


# ── Historique d'un employé précis ──────────────────────────────────────────

class HistoriqueEmployeView(APIView):
    """GET /historique/employe/?employe_id=123 — historique paginé d'un employé."""

    def get(self, request):
        employe_id = request.query_params.get('employe_id')
        if not employe_id:
            return Response({'detail': 'employe_id requis'}, status=status.HTTP_400_BAD_REQUEST)

        qs = get_historique_employe(employe_id)
        return _paginate(request, qs, HistoriquePaiementSerializer)


# ── Mise à jour groupée du statut des attendances ───────────────────────────

class UpdateStatutAttendanceView(APIView):
    """
    PATCH /attendances/update-statut/
    Body: { "ids": [1, 2, 3], "statut_paiement": "PAYE", "statut_attendance": "ARCHIVE" }
    """

    def patch(self, request):
        input_dto = UpdateStatutInputDTO(data=request.data)
        input_dto.is_valid(raise_exception=True)
        data = input_dto.validated_data

        try:
            result = update_statut_bulk(
                ids=data['ids'],
                statut_paiement=data.get('statut_paiement'),
                statut_attendance=data.get('statut_attendance'),
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output = UpdateStatutOutputDTO({
            'message': f"{result['updated']} attendance(s) mis à jour.",
            'updated': result['updated'],
            'ids':     result['ids'],
        })
        return Response(output.data, status=status.HTTP_200_OK)


# ── Création manuelle d'une attendance ──────────────────────────────────────

class CreateAttendanceManuelView(APIView):
    """
    POST /attendances/creer-manuel/
    Body: { "employee_id": "EMP001", "action": "sign_in", ... }
    """

    def post(self, request):
        input_dto = CreateAttendanceManuelInputDTO(data=request.data)
        input_dto.is_valid(raise_exception=True)

        try:
            attendance = create_attendance_manuel(input_dto.validated_data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output = CreateAttendanceOutputDTO({
            'message':           'Attendance créée manuellement.',
            'id':                attendance.id,
            'employee_id':       attendance.employee_id,
            'action':            attendance.action,
            'statut_attendance': attendance.statut_attendance,
        })
        return Response(output.data, status=status.HTTP_201_CREATED)


# ── Liste paginée des attendances par employé ───────────────────────────────

class AttendanceListView(APIView):
    """GET /attendances/?statut_paiement=PAYE&statut_attendance=ARCHIVE — liste paginée."""

    def get(self, request):
        data = get_attendances_par_employe(
            statut_paiement=request.query_params.get('statut_paiement'),
            statut_attendance=request.query_params.get('statut_attendance'),
        )
        return _paginate(request, data, AttendanceParEmployeSerializer)


# ── Détail d'une attendance ─────────────────────────────────────────────────

class AttendanceDetailView(APIView):
    """GET /attendances/<pk>/ — détail d'une attendance précise."""

    def get(self, request, pk):
        try:
            attendance = get_attendance_detail(pk)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(AttendanceSerializer(attendance).data, status=status.HTTP_200_OK)


# ── Statistiques globales (pas de pagination — réponse unique) ──────────────

class StatsView(APIView):
    """GET /stats/ — compteurs globaux pour le dashboard."""

    def get(self, request):
        output = StatsOutputDTO(get_stats_globales())
        return Response(output.data)


# ── Jours cumulés impayés ────────────────────────────────────────────────────

class JoursCumulesView(APIView):
    """GET /jours-cumules/ — liste paginée des dates distinctes d'attendances impayées."""

    def get(self, request):
        dates     = get_jours_cumules_impayes()
        paginator = StandardPagination()
        page      = paginator.paginate_queryset(dates, request)
        return paginator.get_paginated_response(page)


# ── Historique paginé avec stats ─────────────────────────────────────────────

class HistoriqueView(APIView):
    """GET /historique/?page=1&search=...&dept=...&date_debut=...&date_fin=..."""

    def get(self, request):
        qs    = appliquer_filtres_historique(request)
        stats = get_historique_stats(qs)  # calculées AVANT pagination, sur tout le résultat filtré

        paginator = StandardPagination()
        page      = paginator.paginate_queryset(qs, request)
        data      = HistoriquePaiementSerializer(page, many=True).data

        response = paginator.get_paginated_response(data)
        response.data['stats'] = stats  # on ajoute les stats à la réponse paginée
        return response


# ── Historique groupé par jour de paiement ───────────────────────────────────

class HistoriqueParJourPaiementView(APIView):
    """GET /historique/par-jour/?limit=4 — historique regroupé par date de paiement."""

    def get(self, request):
        qs    = appliquer_filtres_historique(request)
        limit = int(request.query_params.get('limit', 4))
        data  = get_historique_par_jour(qs, limit)
        return Response(list(data))


# ── Export PDF de l'historique (pas de pagination — fichier binaire) ────────

class ExportPdfHistoriqueView(APIView):
    """GET /historique/export-pdf/ — génère et renvoie un PDF de l'historique filtré."""

    def get(self, request):
        pdf = generer_pdf_historique(appliquer_filtres_historique(request))

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="historique-paiements.pdf"'
        return response