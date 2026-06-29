from django.http import HttpResponse
from utils.pagination import StandardPagination
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from utils.permissions import IsAdmin
from .models import Portefeuille, HistoriquePaiement
from .serializers import AttendanceParEmployeSerializer, AttendanceSerializer, PortefeuilleSerializer, HistoriquePaiementSerializer
from .services import confirmer_rh, get_attendance_detail, get_attendances_par_employe, marquer_paye,update_statut_bulk,create_attendance_manuel
from .pdf import generer_pdf_portefeuille


# ── Liste paginée avec filtre statut ─────────────────────────────────────────

class PortefeuilleListView(generics.ListAPIView):
    serializer_class = PortefeuilleSerializer
    filter_backends  = [filters.SearchFilter]
    search_fields    = ['employe__nom_complet', 'employe__odoo_id']

    def get_queryset(self):
        qs     = Portefeuille.objects.select_related('employe')
        statut = self.request.query_params.get('statut')
        if statut:
            qs = qs.filter(statut=statut)
        return qs


# ── Détail ────────────────────────────────────────────────────────────────────

class PortefeuilleDetailView(generics.RetrieveDestroyAPIView):
    queryset         = Portefeuille.objects.select_related('employe')
    serializer_class = PortefeuilleSerializer

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAdmin()]
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Actions métier ────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirmer_rh_view(request, pk):
    try:
        pf = Portefeuille.objects.get(pk=pk)
    except Portefeuille.DoesNotExist:
        return Response({'detail': 'Introuvable'}, status=status.HTTP_404_NOT_FOUND)
    pf = confirmer_rh(pf)
    return Response({'statut': pf.statut, 'modifie_le': pf.modifie_le})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def payer_view(request, pk):
    try:
        pf = Portefeuille.objects.get(pk=pk)
    except Portefeuille.DoesNotExist:
        return Response({'detail': 'Introuvable'}, status=status.HTTP_404_NOT_FOUND)
    pf = marquer_paye(pf)
    return Response({'statut': pf.statut, 'modifie_le': pf.modifie_le})


# ── Historique employé ────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historique_employe_view(request):
    employe_id = request.query_params.get('employe_id')
    if not employe_id:
        return Response({'detail': 'employe_id requis'}, status=status.HTTP_400_BAD_REQUEST)
    qs = HistoriquePaiement.objects.filter(employe_id=employe_id)
    s  = HistoriquePaiementSerializer(qs, many=True)
    return Response(s.data)


# ── Export PDF ────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_pdf_view(request, pk):
    try:
        pf = Portefeuille.objects.select_related('employe').get(pk=pk)
    except Portefeuille.DoesNotExist:
        return Response({'detail': 'Introuvable'}, status=status.HTTP_404_NOT_FOUND)
    pdf_bytes = generer_pdf_portefeuille(pf)
    response  = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="portefeuille_{pk}.pdf"'
    return response

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_statut_attendance_view(request):
    """
    PATCH /attendances/update-statut/
    Body:
    {
        "ids": [1, 2, 3],
        "statut_paiement":  "PAYE",
        "statut_attendance": "ARCHIVE"
    }
    """
    ids               = request.data.get('ids', [])
    statut_paiement   = request.data.get('statut_paiement')
    statut_attendance = request.data.get('statut_attendance')

    if not isinstance(ids, list) or not ids:
        return Response(
            {'error': 'Le champ "ids" doit être une liste non vide.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        result = update_statut_bulk(
            ids=ids,
            statut_paiement=statut_paiement,
            statut_attendance=statut_attendance,
        )
        return Response(
            {
                'message': f"{result['updated']} attendance(s) mis à jour.",
                'updated': result['updated'],
                'ids':     result['ids'],
            },
            status=status.HTTP_200_OK
        )

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_attendance_manuel_view(request):
    """
    POST /attendances/creer-manuel/
    Body:
    {
        "employee_id":   "EMP001",
        "employee_name": "Jean Dupont",
        "action":        "sign_in",
        "name":          "2026-06-29T08:00:00Z",
        "worked_hours":  8.5,
        "statut_paiement": "EN_ATTENTE"
    }
    """
    try:
        attendance = create_attendance_manuel(request.data)
        return Response(
            {
                'message':           'Attendance créée manuellement.',
                'id':                attendance.id,
                'employee_id':       attendance.employee_id,
                'action':            attendance.action,
                'statut_attendance': attendance.statut_attendance,
            },
            status=status.HTTP_201_CREATED
        )

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_list_view(request):
    """
    GET /attendances/?statut_paiement=PAYE&statut_attendance=CREATION_AUTO&page=1&limit=10
    """
    statut_paiement   = request.query_params.get('statut_paiement')
    statut_attendance = request.query_params.get('statut_attendance')

    try:
        data = get_attendances_par_employe(
            statut_paiement=statut_paiement,
            statut_attendance=statut_attendance,
        )

        # Pagination
        paginator  = StandardPagination()
        page       = paginator.paginate_queryset(data, request)
        serializer = AttendanceParEmployeSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_detail_view(request, pk):
    """
    GET /attendances/<pk>/
    Retourne le détail d'une attendance.
    """
    try:
        attendance = get_attendance_detail(pk)
        serializer = AttendanceSerializer(attendance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)