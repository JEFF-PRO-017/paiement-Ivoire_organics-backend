def detecter_operateur_ci(phone_number):
    """Déduit le channel NotchPay (ci.orange/ci.mtn/ci.moov) depuis le préfixe du numéro CI."""
    if not phone_number:
        return None
    numero = str(phone_number).replace('+225', '').replace(' ', '')
    if numero.startswith(('07', '08', '09')):
        return 'ci.orange'
    if numero.startswith(('05', '06', '04')):
        return 'ci.mtn'
    return None