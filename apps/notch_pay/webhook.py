from apps.paiements.models import Paiement
    
import hmac
import hashlib
import json

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


def _signature_valide(payload_brut, signature_recue):
    signature_calculee = hmac.new(
        settings.NOTCHPAY_WEBHOOK_SECRET.encode('utf-8'),
        payload_brut,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature_calculee, signature_recue)


@csrf_exempt
@require_POST
def notchpay_webhook(request):
    signature = request.headers.get('X-Notchpay-Signature', '')
    if not _signature_valide(request.body, signature):
        return HttpResponse(status=401)

    event = json.loads(request.body)
    reference = event.get('data', {}).get('reference')

    try:
        paiement = Paiement.objects.get(reference=reference)
    except Paiement.DoesNotExist:
        return HttpResponse(status=404)

    if event.get('type') == 'transfer.complete':
        paiement.statut = 'SUCCESS'
        paiement.date_confirmation = timezone.now()
        paiement.attendances.update(statut_paiement='PAYE', date_validation_paiement=timezone.now())
    elif event.get('type') == 'transfer.failed':
        paiement.statut = 'FAILED'
        paiement.date_confirmation = timezone.now()

    paiement.reponse_brute = event
    paiement.save()
    return HttpResponse('OK')