from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.employes.models import Employe


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_view(request):
    """
    GET /empreinte/verify?employe_id=<id>

    MOCK : retourne toujours verified=True si l'employé existe.

    TODO (driver USB prêt) :
      - Interroger le service local du terminal via subprocess ou socket
      - Comparer avec employe.empreinte_template
      - Retourner verified selon le résultat
    """
    employe_id = request.query_params.get('employe_id')

    if not employe_id:
        return Response({'detail': 'employe_id requis'}, status=400)

    try:
        employe = Employe.objects.get(pk=employe_id, statut='ACTIF')
    except Employe.DoesNotExist:
        return Response({'verified': False, 'message': 'Employé introuvable'}, status=200)

    # ── MOCK ────────────────────────────────────────────────────────────────
    # Simule une vérification réussie après 1 poll (en prod : comparer template)
    return Response({'verified': True, 'employe_id': employe.id})
    # ── FIN MOCK ─────────────────────────────────────────────────────────────
