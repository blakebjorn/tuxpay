import asyncio
import hashlib
import json
import pathlib
from pathlib import Path
from typing import Optional

import bleach
import pdfkit
from jinja2.environment import Environment
from sqlalchemy import and_, or_, select

from modules.coins import ALL_COINS
from modules.models import Payment, Invoice, database

template_file = Path("modules/invoice_template.html")
jinja_env = Environment()
invoice_template = jinja_env.from_string(template_file.read_text())

output_dir = pathlib.Path("data/invoices")
output_dir.mkdir(parents=True, exist_ok=True)

bleach.ALLOWED_TAGS += ['p']


async def get_invoice_pdf_data(invoice_id: int) -> Optional[dict]:
    q = select([
        Invoice.c.name.label("invoice_name"),
        Invoice.c.status.label("invoice_status"),
        Invoice.c.customer_name.label("invoice_customer_name"),
        Invoice.c.customer_email.label("invoice_customer_email"),
        Invoice.c.expiry_date.label("invoice_expiry_date"),
        Invoice.c.amount_cents.label("invoice_amount_cents"),
        Invoice.c.currency.label("invoice_currency"),
        Invoice.c.creation_date.label("invoice_creation_date"),
        Invoice.c.notes_html.label("invoice_notes_html"),
        Invoice.c.contents_html.label("invoice_contents_html"),
        Payment.c.status.label("payment_status"),
        Payment.c.payment_date.label("payment_payment_date"),
        Payment.c.amount_sats,
        Payment.c.paid_amount_sats,
        Payment.c.symbol.label("payment_symbol"),
        Payment.c.address.label("payment_address")]) \
        .select_from(Invoice.outerjoin(Payment, Payment.c.invoice_id == Invoice.c.id)) \
        .where(and_(Invoice.c.id == invoice_id,
                    or_(Payment.c.status.in_(['paid', 'confirmed']),
                        Payment.c.id.is_(None))))
    _data = await database.fetch_one(q)
    if _data is None:
        return None

    data = dict(_data)
    if data['payment_symbol']:
        data['payment_amount_coin'] = ALL_COINS[data['payment_symbol']].sats_to_coin(data.pop('amount_sats'))
        data['payment_paid_amount_coin'] = ALL_COINS[data['payment_symbol']].sats_to_coin(data.pop('paid_amount_sats'))

    for k in ('invoice_expiry_date', 'invoice_creation_date', 'payment_payment_date'):
        data[k] = data[k].strftime("%Y-%m-%d %h:%M:%s") if data[k] else None
    return data


async def build_invoice_pdf(fields: dict) -> Path:
    data_checksum = hashlib.md5(json.dumps(fields).encode()).hexdigest()
    filename = f"Invoice {fields['invoice_name']}.{data_checksum[:4]}.pdf"
    out_file = (output_dir / filename)
    if out_file.exists():
        return out_file

    if fields['invoice_notes_html']:
        fields['invoice_notes_html'] = bleach.clean(fields['invoice_notes_html'])
    if fields['invoice_contents_html']:
        fields['invoice_contents_html'] = bleach.clean(fields['invoice_contents_html'])

    content = invoice_template.render(**fields)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, pdfkit.from_string, content, out_file, {'page-height': '11in',
                                                                             'page-width': '8.5in'})
    return out_file
