import datetime
from typing import List

from fastapi import APIRouter
from fastapi.requests import Request
from modules import config
from modules.authentication import requires_auth
from modules.coins import ALL_COINS
from modules.exchanges import exchangeRates
from modules.helpers import JSONResponse, NOT_FOUND
from modules.models import database, Payment
from modules.payments import TuxPayment
from views.admin_invoice import create_invoice_from_payload
from views.api_models import PaymentCreationModel, PaymentAdminReadModel

router = APIRouter(prefix='/api')


@router.get('/admin/payment/{payment_id}', tags=['admin', 'payment'])
@requires_auth
async def admin_payment_get(payment_id: int, _: Request):
    ret = await database.fetch_one(Payment.select().where(Payment.c.id == payment_id))
    return JSONResponse({"payment": ret}) if ret else NOT_FOUND


@router.get('/admin/payments', response_model=List[PaymentAdminReadModel], tags=['admin', 'payment'])
@requires_auth
async def admin_get_payments(_: Request, limit: int = 50, offset: int = 0):
    ret = await database.fetch_all(Payment.select().order_by(Payment.c.id.desc()).limit(limit).offset(offset))
    payments = [dict(x) for x in ret]
    for x in payments:
        x['amount_coin'] = ALL_COINS[x['symbol']].sats_to_coin(x['amount_sats'])
        x['paid_amount_coin'] = ALL_COINS[x['symbol']].sats_to_coin(x['paid_amount_sats'])
    return JSONResponse(payments)


@router.post('/admin/payment', tags=['admin', 'payment'])
@requires_auth
async def admin_payment_creation(payload: PaymentCreationModel, _: Request):
    """
    Creates a payment + invoice all in one call
    """
    # Requires EITHER: 'currency' + 'fiat_amount' OR 'amount_sats'
    symbol = payload.symbol
    if not symbol or symbol not in ALL_COINS:
        return JSONResponse({"error": "must pass `symbol` of an enabled coin"}, status_code=400)

    if 'amount_sats' in payload and "amount_cents" in payload:
        return JSONResponse({"error": "cannot specify both 'fiat_amount' and 'amount_sats'"},
                            status_code=400)

    currency = payload.currency or config.get("default_currency", namespace="CURRENCY", default="USD")
    if currency not in (await exchangeRates.currencies):
        return JSONResponse({"error": f"bad currency code - {currency}"}, status_code=400)

    if payload.amount_sats is not None and payload.amount_sats > 0:
        payload.amount_cents = int(round(
            await exchangeRates.get_reverse_exchange_amount(payload.amount_sats, symbol, currency) * 100
        ))
    elif payload.amount_cents is not None and payload.amount_cents > 0:
        payload.amount_sats = await exchangeRates.get_exchange_amount(symbol, payload.amount_cents / 100.0, currency)
    else:
        return JSONResponse({"error": "must pass either 'amount_cents' or 'amount_sats'"}, status_code=400)

    now = datetime.datetime.utcnow()
    expiry = datetime.datetime.utcfromtimestamp(payload.expiry_date) if payload.expiry_date else \
        now + datetime.timedelta(minutes=int(config.get("payment_expiry_min", default=15)))
    if expiry < now:
        return JSONResponse({"error": "expiry date must be in the future"}, status_code=400)

    inv = await create_invoice_from_payload(payload)
    payment = await TuxPayment.create(symbol, inv, amount_sats=payload.amount_sats)
    await payment.insert()

    return JSONResponse({"invoice": inv, "payment": payment.to_dict()})
