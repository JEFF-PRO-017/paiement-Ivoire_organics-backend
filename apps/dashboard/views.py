from django.db.models import Sum
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.employes.models import Employe
from apps.portefeuilles.models import Portefeuille, HistoriquePaiement
from .pdf import generer_pdf_historique


def _appliquer_filtres(request):
    qs = HistoriquePaiement.objects.select_related('employe', 'portefeuille').order_by('-date_paiement')
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats_view(request):
    nombre_employes = Employe.objects.filter(statut='ACTIF').count()
    agg          = Portefeuille.objects.filter(statut__in=['EN_ATTENTE', 'IMPAYE']).aggregate(total_jours=Sum('nombre_jours_impayes'))
    pfs          = Portefeuille.objects.filter(statut__in=['EN_ATTENTE', 'IMPAYE'])
    somme_totale = sum(p.montant_total for p in pfs)
    return Response({'nombre_employes': nombre_employes, 'total_jours_cumules': agg['total_jours'] or 0, 'somme_totale_a_payer': somme_totale})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def jours_cumules_view(request):
    pfs   = Portefeuille.objects.filter(statut__in=['EN_ATTENTE', 'IMPAYE'])
    dates = [d for pf in pfs for d in pf.periodes_paiement]
    return Response(sorted(set(dates)))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historique_view(request):
    # limit = int(request.query_params.get('limit', 4))
    # qs    = _appliquer_filtres(request).values('id', 'date_paiement','nombre_jours','montant_total','employe__nom_complet','employe__id','employe__departement','portefeuille__statut')[:limit]
    qs    = _appliquer_filtres(request).values('id', 'date_paiement','nombre_jours','montant_total','employe__nom_complet','employe__id','employe__departement','portefeuille__statut')
    return Response(list(qs))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_pdf_historique_view(request):
    pdf      = generer_pdf_historique(_appliquer_filtres(request))
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="historique-paiements.pdf"'
    return response