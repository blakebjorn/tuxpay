from urllib.parse import urlencode

from modules.qr_codes import make_qr_code


def bip21_qr_code(address, amount, label=None, message=None, intent="bitcoin:"):
    assert amount > 0

    params = {
        "amount": amount,
        "label": label,
        "message": message
    }

    urn = f"{intent}{address}?{urlencode({k: v for k, v in params.items() if v})}"
    return make_qr_code(urn)
