from django.http import HttpResponse
from apps.paiements.services.pdf import generer_pdf_historique
from apps.paiements.services.signalement import create_signalement
from core.mixins import AvecSiteMixin, avec_site
from rest_framework.generics import ListAPIView, ValidationError
from rest_framework.views import APIView

from core.response import ApiResponse
from apps.odoo_attendance.models import Attendance

from .dto import (
    CreateAttendanceManuelInputDTO, CreateAttendanceOutputDTO, CreateSignalementInputDTO, CreateSignalementOutputDTO,
    StatsOutputDTO, UpdateStatutInputDTO, UpdateStatutOutputDTO,
)
from .serializers import (
    AttendanceParEmployeSerializer, AttendanceSerializer, PaiementSerializer,
)
from .services.services import (
    appliquer_filtres_historique, create_attendance_manuel, get_attendance_detail,
    get_attendances_par_employe, get_historique_employe, get_historique_par_jour,
    get_historique_stats, get_jours_cumules_impayes, get_stats_globales,
    update_statut_bulk,
)


class AttendanceView(AvecSiteMixin, ListAPIView):
    """
    GET  /attendances/?statut_paiement=PAYE&statut_attendance=ARCHIVE
    POST /attendances/
    PATCH /attendances/
    """
    serializer_class = AttendanceParEmployeSerializer
    site_requis = False

    def get_queryset(self):
        if not self.site:
            return Attendance.objects.none()
        qs = Attendance.objects.select_related('employe').filter(employe__site_travail=self.site)
        return get_attendances_par_employe(
            qs,
            statut_paiement=self.request.query_params.get('statut_paiement'),
            statut_attendance=self.request.query_params.get('statut_attendance'),
        )

    def post(self, request):
        input_dto = CreateAttendanceManuelInputDTO(data=request.data)
        input_dto.is_valid(raise_exception=True)      # ← appel seul, ignore le retour bool
        data = input_dto.validated_data                # ← récupère les données ICI, séparément
        data['statut_paiement'] = 'EN_ATTENTE'

        attendance = create_attendance_manuel(data)

        output = CreateAttendanceOutputDTO({
            'id':                attendance.id,
            'action':            attendance.action,
            'statut_paiement':   attendance.statut_paiement,
            'statut_attendance': attendance.statut_attendance,
        })
        return ApiResponse.success(
            data=output.data,
            message="Attendance créée manuellement.",
            status_code=201
        )

    def patch(self, request):
        input_dto = UpdateStatutInputDTO(data=request.data)
        input_dto.is_valid(raise_exception=True)
        data = input_dto.validated_data

        result = update_statut_bulk(
            ids=data['ids'],
            statut_paiement=data.get('statut_paiement'),
            statut_attendance=data.get('statut_attendance'),
        )

        output = UpdateStatutOutputDTO({
            'updated': result['updated'],
            'ids':     result['ids'],
            'message': f"{result['updated']} attendance(s) mis à jour.",

        })
        return ApiResponse.success(
            data=output.data,
            message=f"{result['updated']} attendance(s) mis à jour."
        )


class AttendanceDetailView(APIView):
    """GET /attendances/<pk>/"""

    @avec_site()
    def get(self, request, pk, site):
        # ValueError levée par get_attendance_detail -> transformée en 400 par le handler global
        # Si vous voulez un vrai 404 ici, levez plutôt Http404 ou NotFound dans le service
        attendance = get_attendance_detail(pk, site=site)
        return ApiResponse.success(data=AttendanceSerializer(attendance).data)


class HistoriqueEmployeView(ListAPIView):
    """GET /employe/?employe_id=123"""
    serializer_class = PaiementSerializer

    def get_queryset(self):
        employe_id = self.request.query_params.get('employe_id')
        if not employe_id or not employe_id.isdigit():
            raise ValidationError({'employe_id': 'requis et doit être un entier'})
        return get_historique_employe(employe_id)


class HistoriqueView(AvecSiteMixin, ListAPIView):
    """
    GET /historique/?page=1&search=...&dept=...&date_debut=...&date_fin=...
    """
    serializer_class = PaiementSerializer

    def get_queryset(self):
        return appliquer_filtres_historique(self.request, site=self.site)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # response.data = {success, message, data: {results, pagination}, errors}
        response.data['data']['stats'] = get_historique_stats(self.get_queryset())
        return response


class HistoriqueParJourPaiementView(APIView):
    """GET /historique/par-jour/?limit=4 (pas paginé)"""

    @avec_site(on_site_manquant=lambda self, request: ApiResponse.success(data=[]))
    def get(self, request, site):
        qs    = appliquer_filtres_historique(request, site=site)
        limit = int(request.query_params.get('limit', 4))
        return ApiResponse.success(data=list(get_historique_par_jour(qs, limit)))


class ExportPdfHistoriqueView(APIView):
    """GET /historique/export-pdf/ — reste en HttpResponse (fichier binaire, pas du JSON)"""

    @avec_site()
    def get(self, request, site):
        qs  = appliquer_filtres_historique(request, site=site)
        pdf = generer_pdf_historique(qs)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="historique-paiements.pdf"'
        return response


class StatsView(APIView):
    """GET /stats/ (pas de pagination)"""

    @avec_site()
    def get(self, request, site):
        qs = Attendance.objects.select_related('employe').filter(employe__site_travail=site)
        return ApiResponse.success(data=StatsOutputDTO(get_stats_globales(qs)).data)


class JoursCumulesView(AvecSiteMixin, ListAPIView):
    """GET /jours-cumules/"""
    site_requis = False

    def get_queryset(self):
        return get_jours_cumules_impayes(site=self.site) if self.site else []

    def list(self, request, *args, **kwargs):
        return ApiResponse.success(data=self.get_queryset())



class SignalementView(APIView):
    """POST /signalements/ — signalement d'un utilisateur non-admin (création/suppression)."""

    def post(self, request):
        input_dto = CreateSignalementInputDTO(data=request.data)
        input_dto.is_valid(raise_exception=True)
        data = input_dto.validated_data

        signalement = create_signalement(
            employe_id=data['employe_id'],
            type_demande=data['type_demande'],
            jour=data['jour'],
            raison=data['raison'],
            demandeur=request.user,
        )

        output = CreateSignalementOutputDTO({
            'id': signalement.id,
            'type_demande': signalement.type_demande,
            'jour': signalement.jour,
            'attendance_id': signalement.attendance_id,
            'statut_attendance': signalement.attendance.statut_attendance if signalement.attendance else None,
        })
        return ApiResponse.success(
            data=output.data,
            message="Signalement envoyé à la maintenance.",
            status_code=201,
        )