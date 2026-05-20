from django.db.models import Count, Sum
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.employes.models import Employe
from apps.portefeuilles.models import Portefeuille, HistoriquePaiement
from .pdf import generer_pdf_historique
from django.core.paginator import Paginator, EmptyPage

def _appliquer_filtres(request):
    qs = (
        HistoriquePaiement.objects
        .select_related('employe', 'portefeuille')
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
    # ── Pagination ─────────────────────────────────────────────────────────────
    try:
        page      = max(1, int(request.query_params.get('page', 1)))
        page_size = min(100, max(1, int(request.query_params.get('page_size', 10))))
    except (ValueError, TypeError):
        page, page_size = 1, 10

    qs = _appliquer_filtres(request)

    # ── Stats (calculées sur le queryset filtré, avant pagination) ─────────────
    from django.db.models import Sum, Avg, Count
    stats_qs = qs.aggregate(
        total   = Sum('montant_total'),
        moyenne = Avg('montant_total'),
        count   = Count('id'),
    )
    nb_employes = qs.values('employe_id').distinct().count()

    # ── Page demandée ──────────────────────────────────────────────────────────
    paginator = Paginator(
        qs.values(
            'id', 'date_paiement', 'nombre_jours', 'montant_total',
            'employe__nom_complet', 'employe__id', 'employe__departement',
            'portefeuille__statut','portefeuille__id'
        ),
        page_size,
    )

    try:
        current_page = paginator.page(page)
    except EmptyPage:
        current_page = paginator.page(paginator.num_pages)

    return Response({
        # résultats de la page
        'results':     list(current_page.object_list),
        # méta pagination
        'page':        current_page.number,
        'page_size':   page_size,
        'total_pages': paginator.num_pages,
        'total_count': paginator.count,
        # stats sur le filtrage complet
        'stats': {
            'total':    stats_qs['total']   or 0,
            'moyenne':  round(stats_qs['moyenne'] or 0),
            'count':    stats_qs['count']   or 0,
            'employes': nb_employes,
        },
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historique_par_jour_paiement_view(request):
    qs = _appliquer_filtres(request)
    limit = request.query_params.get('limit',4)
    data = (
        qs.values('date_paiement')[:int(limit)]
        .annotate(total=Sum('montant_total'), count=Count('id'))
    )
    return Response(list(data))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_pdf_historique_view(request):
    pdf      = generer_pdf_historique(_appliquer_filtres(request))
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="historique-paiements.pdf"'
    return response