import datetime
from typing import List

from fastapi import APIRouter
from fastapi.requests import Request
from pydantic import BaseModel
from sqlalchemy import select, or_

from modules.authentication import requires_auth
from modules.helpers import JSONResponse
from modules.models import database, Invoice

router = APIRouter(prefix='/api')


class DashboardInvoice(BaseModel):
    id: int
    creation_date: float
    expiry_date: float
    payment_date: float
    amount_cents: int
    currency: str
    status: str


class SummaryResponse(BaseModel):
    count: int
    dollars: float


class SummaryResponseWithInvoices(BaseModel):
    count: int
    dollars: float
    invoices: List[DashboardInvoice]


class DashboardResponse(BaseModel):
    created: SummaryResponse
    paid: SummaryResponse
    expired: SummaryResponseWithInvoices
    open: List[DashboardInvoice]



@router.get('/admin/dashboard', response_model=DashboardResponse, tags=['admin'])
@requires_auth
async def admin_dashboard(_: Request):
    """
    Returns a summary of the last 30 days worth of invoices and payments
    :return:
    """
    now = datetime.datetime.utcnow()
    last_30 = now - datetime.timedelta(days=30)
    invoices = await database.fetch_all(select([Invoice.c.id, Invoice.c.creation_date, Invoice.c.expiry_date,
                                                Invoice.c.payment_date, Invoice.c.amount_cents,
                                                Invoice.c.currency, Invoice.c.status])
                                        .select_from(Invoice)
                                        .where(or_(Invoice.c.creation_date >= last_30,
                                                   Invoice.c.payment_date >= last_30,
                                                   Invoice.c.expiry_date >= now)))
    created_n = 0
    created_cents = 0.0
    paid_n = 0
    paid_cents = 0.0
    expired = []
    expired_n = 0
    expired_cents = 0.0
    open_inv = []
    for invoice in invoices:
        if invoice['creation_date'] >= last_30:
            created_n += 1
            created_cents += invoice['amount_cents']

        if invoice['payment_date'] and invoice['payment_date'] >= last_30:
            paid_n += 1
            paid_cents += invoice['amount_cents']
        elif invoice['status'] == 'expired':
            expired_n += 1
            expired_cents += invoice['amount_cents']
            expired.append(invoice)
        else:
            open_inv.append(invoice)

    return JSONResponse({
        "created": {"count": created_n, "dollars": round(created_cents / 100, 2)},
        "paid": {"count": paid_n, "dollars": round(paid_cents / 100, 2)},
        "expired": {"count": expired_n, "dollars": round(expired_cents / 100, 2), "invoices": expired},
        "open": open_inv
    })
