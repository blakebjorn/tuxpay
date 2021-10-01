import asyncio
from typing import List

from fastapi import APIRouter, Query
from fastapi.requests import Request
from fastapi.responses import FileResponse
from jwt import DecodeError as JwtDecodeError
from pydantic import BaseModel

from modules.authentication import from_short_jwt
from modules.bip21 import bip21_qr_code
from modules.coins import ALL_COINS
from modules.helpers import JSONResponse, NOT_FOUND, NOT_AUTHENTICATED
from modules.models import Payment, database, Invoice
from modules.payments import TuxPayment
from modules.pdf import build_invoice_pdf, get_invoice_pdf_data
from views.api_models import InvoiceReadModel, PaymentCustomerReadModel
from views.utils import get_coins_raw, CoinResponse

router = APIRouter(prefix='/api')


async def load_invoice_from_token(token: str):
    try:
        payload = from_short_jwt(token)
        invoice = await database.fetch_one(Invoice.select().where(Invoice.c.id == payload['id']))
    except (ValueError, KeyError, JwtDecodeError):
        return None
    if invoice is not None:
        invoice = dict(invoice)
        invoice['token'] = token
    return invoice


class InvoiceGetResponse(BaseModel):
    coins: CoinResponse
    payments: List[PaymentCustomerReadModel]
    invoice: InvoiceReadModel


@router.get('/invoice', response_model=InvoiceGetResponse, tags=['invoice'])
async def invoice_get(token: str = Query(None, title="Token associated with the invoice", example="")):
    invoice = await load_invoice_from_token(token)
    if invoice is None:
        return JSONResponse({"error": "not found"}, status_code=404)

    coins, payments = await asyncio.gather(
        get_coins_raw(),
        database.fetch_all(Payment.select().where(Payment.c.invoice_id == invoice['id']))
    )
    for i, payment in enumerate(payments):
        payments[i] = dict(payment)
        if payment['status'] == 'pending':
            payments[i]['qr_code'] = bip21_qr_code(
                address=payment['address'],
                amount=ALL_COINS[payment['symbol']].sats_to_coin(payment['amount_sats']),
                label=f"Invoice #{payment['invoice_id']} Payment",
                intent=ALL_COINS[payment['symbol']].bip21_intent)
    return JSONResponse({"invoice": invoice, "coins": coins, "payments": payments})


class TuxPaymentModel(PaymentCustomerReadModel):
    invoice: InvoiceReadModel


@router.put('/invoice', response_model=TuxPaymentModel, tags=['invoice', 'payment'])
async def invoice_put(request: Request):
    """
    Creates a new payment against an open payment
    """
    payload = await request.json()
    if 'token' not in payload:
        return NOT_FOUND
    invoice = await load_invoice_from_token(payload['token'])
    tux_payment = await TuxPayment.create(payload['payment_coin'], invoice)
    await tux_payment.insert()

    return JSONResponse({"payment": tux_payment.to_dict()})


@router.get('/invoice/download',
            responses={200: {"content": {"application/pdf": {}}, "description": "PDF copy of the passed invoice."}},
            tags=['invoice', 'payment'])
async def invoice_download(request: Request, invoice_id: int = None, token: str = None):
    """
    Downloads a PDF copy of the given invoice.
    Passing `invoice_id` requires admin authentication, passing `token` does not.
    """
    if token is not None:
        payload = from_short_jwt(token)
        invoice_id = payload['id']
    elif invoice_id is not None:
        if not request.user.is_authenticated:
            return NOT_AUTHENTICATED

    pdf_data = await get_invoice_pdf_data(invoice_id)
    if pdf_data is None:
        return NOT_FOUND

    pdf_file = await build_invoice_pdf(pdf_data)
    return FileResponse(pdf_file, filename=pdf_file.name.split(".")[0] + ".pdf")
