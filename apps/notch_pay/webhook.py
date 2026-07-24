import hmac
import hashlib
import json

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.paiements.models import Paiement



def verify_webhook_signature(payload, signature, secret):
    """Recalcule la signature HMAC-SHA256 et la compare à celle envoyée par NotchPay."""
    calculated_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    # compare_digest évite les attaques par timing (comparaison à temps constant)
    return hmac.compare_digest(calculated_signature, signature or '')


@csrf_exempt
@require_POST
def notchpay_webhook(request):
    payload = request.body.decode('utf-8')
    signature = request.headers.get('X-Notch-Signature')

    if not verify_webhook_signature(payload, signature, settings.NOTCHPAY_WEBHOOK_SECRET):
        return HttpResponse('Invalid signature', status=400)

    event = json.loads(payload)
    reference = event.get('data', {}).get('reference')

    try:
        paiement = Paiement.objects.get(reference=reference)
    except Paiement.DoesNotExist:
        return HttpResponse('Paiement introuvable', status=404)

    event_type = event.get('type', '')
    if event_type == 'transfer.complete':
        paiement.statut = 'SUCCESS'
        paiement.date_confirmation = timezone.now()
        paiement.attendances.update(statut_paiement='PAYE', date_validation_paiement=timezone.now())
    elif event_type == 'transfer.failed':
        paiement.statut = 'FAILED'
        paiement.date_confirmation = timezone.now()

    paiement.reponse_brute = event
    paiement.save()
    return HttpResponse('Webhook received', status=200)