import asyncio
import datetime
import uuid
from typing import List

from fastapi import APIRouter
from fastapi.requests import Request
from pydantic import BaseModel

from modules.authentication import requires_auth, to_short_jwt
from modules.coins import ALL_COINS
from modules.config import get_app_secret
from modules.helpers import JSONResponse, NOT_FOUND, left_pad
from modules.models import database, Invoice, Payment
from modules.payments import parse_notes
from views.api_models import InvoiceReadModel, PaymentAdminReadModel, InvoiceCreationModel

router = APIRouter(prefix='/api')


class AdminInvoiceLookupResponse(BaseModel):
    invoice: InvoiceReadModel
    payments: List[PaymentAdminReadModel]


class AdminInvoiceCreationResponse(BaseModel):
    invoice: InvoiceReadModel



@router.get('/admin/invoice/{invoice_id}', response_model=AdminInvoiceLookupResponse, tags=['admin', 'invoice'])
@requires_auth
async def admin_invoice_get(invoice_id: int, _: Request):
    """
    Returns an invoice and all associated payment details
    """
    invoice, payments = await asyncio.gather(
        database.fetch_one((Invoice.select().where(Invoice.c.id == invoice_id))),
        database.fetch_all((Payment.select().where(Payment.c.invoice_id == invoice_id))),
    )
    if invoice is None:
        return NOT_FOUND

    invoice = dict(invoice)
    invoice['token'] = to_short_jwt({"id": invoice['id']})

    payments = [dict(x) for x in payments]
    for x in payments:
        x['amount_coin'] = ALL_COINS[x['symbol']].sats_to_coin(x['amount_sats'])
        x['paid_amount_coin'] = ALL_COINS[x['symbol']].sats_to_coin(x['paid_amount_sats'])
    return JSONResponse({"invoice": invoice, "payments": payments})



@router.get('/admin/invoice', response_model=List[InvoiceReadModel], tags=['admin', 'invoice'])
@requires_auth
async def admin_invoices( _: Request, limit: int = 50, offset: int = 0):
    """
    Fetches a list of invoices
    """
    invoices = await database.fetch_all(Invoice.select()
                                        .order_by(Invoice.c.creation_date.desc())
                                        .limit(limit)
                                        .offset(offset * limit))
    out = []
    for i, inv in enumerate(invoices):
        inv = dict(inv)
        inv['token'] = to_short_jwt({"id": inv['id']})
        out.append(inv)
    return JSONResponse(out)


async def create_invoice_from_payload(payload: InvoiceCreationModel):
    app_secret = get_app_secret()
    if not app_secret:
        raise KeyError("application secret not set, cannot issue partial invoice")

    inv_uuid = str(uuid.uuid4())
    expiry = datetime.datetime.utcfromtimestamp(payload.expiry_date) if payload.expiry_date else None

    currency = payload.currency
    amount_cents = payload.amount_cents

    notes = parse_notes(payload.notes, payload.notes_html)
    contents = parse_notes(payload.contents, payload.contents_html)
    inv = dict(
        uuid=inv_uuid,
        amount_cents=amount_cents,
        currency=currency,
        creation_date=datetime.datetime.utcnow(),
        expiry_date=expiry,
        status="pending",
        name=payload.name or None,
        customer_name=payload.customer_name or None,
        customer_email=payload.customer_email or None,
        notes=notes['raw'],
        notes_html=notes['html'],
        contents=contents['raw'],
        contents_html=contents['html'],
    )

    inv['id'] = await database.execute(Invoice.insert().values(**inv))
    if inv['name'] is None:
        inv['name'] = f"#INV-{left_pad(str(inv['id']), 5)}"
        await database.execute(Invoice.update().where(Invoice.c.id == inv['id'])
                               .values(name=f"#INV-{left_pad(str(inv['id']), 5)}"))
    return inv



@router.post('/admin/invoice', response_model=AdminInvoiceCreationResponse, tags=['admin', 'invoice'])
@requires_auth
async def admin_invoice_creation(payload: InvoiceCreationModel, _: Request):
    """
    Creates an Invoice
    """
    inv = await create_invoice_from_payload(payload)
    inv['token'] = to_short_jwt({"id": inv['id']})
    return JSONResponse({"invoice": inv})
