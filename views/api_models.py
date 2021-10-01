from typing import Optional

from pydantic import BaseModel, Field


class InvoiceCreationModel(BaseModel):
    currency: str = Field("USD", title="Fiat currency type")
    amount_cents: int = Field(None, title="Invoice amount, in cents", example=999)
    expiry_date: float = Field(None, title="Expiration timestamp", example=1699999999.5)
    name: Optional[str] = Field(None, title="Name assigned to the invoice, if blank, will be assigned the name "
                                            "`#INV-XXXXX` where X is the invoice ID, left padded with zeros to a "
                                            "minimum of 5 characters", max_length=200)

    customer_name: str = Field(None, title="Customer Name", example="Test User")
    customer_email: str = Field(None, title="Customer Email", example="Customer Email")

    notes: Optional[str] = Field(None,
                                 title="Notes to be printed on the invoice. "
                                       "If only one of `notes`/`notes_html` is provided, the value of one "
                                       "will be inferred from the other",
                                 example=r"Notes\nin\nraw\ntext")

    notes_html: Optional[str] = Field(None,
                                      title="Notes to be printed on the invoice. "
                                            "If only one of `notes`/`notes_html` is provided, the value of one "
                                            "will be inferred from the other",
                                      example="<p>Notes</p><p>in</p><p>raw</p><p>text</p>")

    contents: Optional[str] = Field(None,
                                    title="Contents (e.g. line items) in plain text to be printed on the invoice. "
                                          "If only one of `contents`/`contents_html` is provided, the value of one "
                                          "will be inferred from the other",
                                    example=r"- #2 Pencil\n- Bic Pen\n- Yellow Highlighter")

    contents_html: Optional[str] = Field(None,
                                         title="Contents (e.g. line items) in plain text to be printed on the invoice. "
                                               "If only one of `contents`/`contents_html` is provided, the value of one "
                                               "will be inferred from the other",
                                         example="<ul><li>#2 Pencil</li><li>Bic Pen</li><li>Yellow Highlighter</li></ul>")


class InvoiceReadModel(InvoiceCreationModel):
    id: int = Field(None, title="The invoice's ID", example=53)
    uuid: int = Field(None, title="Unique identifier of the invoice", example="c0e7635e-c547-4068-ad04-2b96263ce201")
    creation_date: float = Field(None, title="Creation timestamp", example=1649999999.5)
    payment_date: float = Field(None, title="Payment timestamp", example=1679999999.5)
    status: str = Field(None, title="Invoice payment status, one of `pending`, `expired`, `paid`, or `confirmed`",
                        example="confirmed")
    token: str = Field(None,
                       title="Token used to facilitate invoice payment. "
                             "NOTE: the algorithm is truncated from the front of the "
                             "JWT to minimize character count",
                       example="eyJpZCI6Nn0.kqGv1YFHpoENA0iIwm_1BopND6KsIzuNYaKTDX_xV1Q")


class PaymentBaseModel(BaseModel):
    invoice_id: int = Field(None, title="The parent invoice's ID", example=53)
    symbol: str = Field(None, title="Payment coin identifier", example="tBTC")
    expiry_date: float = Field(None, title="Expiration timestamp", example=1624497930.8)
    amount_sats: int = Field(None, title="Amount to be paid to this address", example=1299)


class PaymentCustomerReadModel(PaymentBaseModel):
    id: int = Field(None, title="The payment's ID", example=16)
    uuid: str = Field(None, title="Payment UUID", example="f3ff3ba1-3c7d-4189-9a5e-e2a20ab86a3d")
    creation_date: float = Field(None, title="Creation timestamp", example=1624497030.8)
    creation_height: int = Field(None, title="Blockheight at the time of address generation", example=2006107)
    address: str = Field(None, title="Payment Address", example="tb1q73fcynsq0l0cl842pwp0x4f8epsqslaj2acfw6")
    status: str = Field(None, title="One of `pending`, `expired`, `paid`, or `confirmed`", example="paid")

    payment_date: float = Field(None, title="Payment timestamp", example=1679999999.5)
    last_update: float = Field(None, title="Update timestamp", example=1679999999.5)

    amount_coin: float = Field(None, title="Floating point representation of `amount_sats`", example=0.00001299)
    paid_amount_sats: int = Field(None, title="How much has been paid out to this address since payment creation",
                                  example=1299)
    paid_amount_coin: float = Field(None, title="Floating point representation of `paid_amount_sats`",
                                    example=0.00001299)
    qr_code: float = Field(None,
                           title="BIP-21 compatible QR Code as a Base64 encoded PNG - only returned for active payment addresses",
                           example="data:image/png;base64, Af9sad21jdsa[...] ")

    invoice: InvoiceReadModel


class PaymentAdminReadModel(PaymentCustomerReadModel):
    scripthash: str = Field(None, title="Scripthash of the payment",
                            example="b2c687e687b46f6491e9bea9e49dd54f09cb547f33935b9d74cebc320a81e053")
    derivation_path: str = Field(None, title="Derivation path of the address", example="84h/1h/0h/0/8")
    derivation_account: int = Field(None, title="Derivation account of the address", example=0)
    derivation_index: int = Field(None, title="Derivation index of the address", example=8)


class PaymentCreationModel(InvoiceCreationModel):
    symbol: str = Field(None, title="Payment Coin (e.g. BTC, LTC, etc)")
    amount_sats: int = Field(None, title="Payment amount in the minimum denomination of the coin (Satoshis)")


tags_metadata = [
    {
        "name": "authentication",
        "description": "Authentication flow.",
    },
    {
        "name": "admin",
        "description": "Admin endpoints - Required for creating new invoices and payments, and all admin panel "
                       "functionality."
    },
    {
        "name": "invoice",
        "description": "Endpoints pertaining to invoice creation, reading, and payment"
    },
    {
        "name": "payment",
        "description": "Endpoints pertaining to payment creation and reading"
    },
]
