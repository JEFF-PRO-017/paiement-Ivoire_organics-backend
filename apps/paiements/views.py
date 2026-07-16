from django.http import HttpResponse
from utils.mixins import AvecSiteMixin, avec_site
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.odoo_attendance.models import Attendance
from apps.paiements.pdf import generer_pdf_historique

from .dto import (
    CreateAttendanceManuelInputDTO, CreateAttendanceOutputDTO,
    StatsOutputDTO, UpdateStatutInputDTO, UpdateStatutOutputDTO,
)
from .serializers import (
    AttendanceParEmployeSerializer, AttendanceSerializer, HistoriquePaiementSerializer,
)
from .services import (
    appliquer_filtres_historique, create_attendance_manuel, get_attendance_detail,
    get_attendances_par_employe, get_historique_employe, get_historique_par_jour,
    get_historique_stats, get_jours_cumules_impayes, get_stats_globales,
    update_statut_bulk,
)


class AttendanceView(AvecSiteMixin, ListAPIView):
    """
    GET  /attendances/?statut_paiement=PAYE&statut_attendance=ARCHIVE
    Liste paginée des attendances du site courant, groupées par employé.

    POST /attendances/
    Body: { "employee_id": "EMP001", "action": "sign_in", ... }
    Crée une attendance manuellement.
    """
    serializer_class = AttendanceParEmployeSerializer
    site_requis = False  # pas de site -> liste vide au lieu d'une erreur 400

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
        input_dto.is_valid(raise_exception=True)

        try:
            attendance = create_attendance_manuel(input_dto.validated_data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        output = CreateAttendanceOutputDTO({
            'message':           'Attendance créée manuellement.',
            'id':                attendance.id,
            'action':            attendance.action,
            'statut_attendance': attendance.statut_attendance,
        })
        return Response(output.data, status=status.HTTP_201_CREATED)


class AttendanceDetailView(APIView):
    """
    GET /attendances/<pk>/
    Détail d'une attendance précise (doit appartenir au site courant).
    """

    @avec_site()
    def get(self, request, pk, site):
        try:
            attendance = get_attendance_detail(pk, site=site)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(AttendanceSerializer(attendance).data)


class UpdateStatutAttendanceView(APIView):
    """
    PATCH /attendances/update-statut/
    Body: { "ids": [1, 2, 3], "statut_paiement": "PAYE", "statut_attendance": "ARCHIVE" }
    Met à jour le statut de plusieurs attendances en une fois.
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
        return Response(output.data)


class HistoriqueEmployeView(ListAPIView):
    """
    GET /employe/?employe_id=123
    Historique paginé des paiements d'un employé précis (tous sites).
    """
    serializer_class = HistoriquePaiementSerializer

    def get_queryset(self):
        employe_id = self.request.query_params.get('employe_id')
        if not employe_id or not employe_id.isdigit():
            raise ValidationError({'detail': 'employe_id requis et doit être un entier'})
        return get_historique_employe(employe_id)


class HistoriqueView(AvecSiteMixin, ListAPIView):
    """
    GET /historique/?page=1&search=...&dept=...&date_debut=...&date_fin=...
    Historique paginé des paiements du site courant, avec stats globales
    calculées sur tout le résultat filtré (pas juste la page affichée).
    """
    serializer_class = HistoriquePaiementSerializer

    def get_queryset(self):
        return appliquer_filtres_historique(self.request, site=self.site)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['stats'] = get_historique_stats(self.get_queryset())
        return response


class HistoriqueParJourPaiementView(APIView):
    """
    GET /historique/par-jour/?limit=4
    Historique du site courant, regroupé par date de paiement (pas paginé).
    """

    @avec_site(on_site_manquant=lambda self, request: Response([]))
    def get(self, request, site):
        qs    = appliquer_filtres_historique(request, site=site)
        limit = int(request.query_params.get('limit', 4))
        return Response(list(get_historique_par_jour(qs, limit)))


class ExportPdfHistoriqueView(APIView):
    """
    GET /historique/export-pdf/
    Génère et renvoie un PDF de l'historique filtré du site courant.
    """

    @avec_site()
    def get(self, request, site):
        qs  = appliquer_filtres_historique(request, site=site)
        pdf = generer_pdf_historique(qs)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="historique-paiements.pdf"'
        return response


class StatsView(APIView):
    """
    GET /stats/
    Compteurs globaux du dashboard pour le site courant (pas de pagination).
    """

    @avec_site()
    def get(self, request, site):
        qs = Attendance.objects.select_related('employe').filter(employe__site_travail=site)
        return Response(StatsOutputDTO(get_stats_globales(qs, site=site)).data)


class JoursCumulesView(AvecSiteMixin, ListAPIView):
    """
    GET /jours-cumules/
    Liste paginée des dates distinctes d'attendances impayées du site courant.
    Pas de serializer : ce sont juste des dates brutes.
    """
    site_requis = False  # pas de site -> liste vide au lieu d'une erreur 400

    def get_queryset(self):
        return get_jours_cumules_impayes(site=self.site) if self.site else []

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        if page is not None:
            return self.get_paginated_response(page)
        return Response(self.get_queryset())