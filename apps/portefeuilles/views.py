from django.http import HttpResponse
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from utils.permissions import IsAdmin
from .models import Portefeuille, HistoriquePaiement
from .serializers import PortefeuilleSerializer, HistoriquePaiementSerializer
from .services import confirmer_rh, marquer_paye
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
