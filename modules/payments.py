import asyncio
import datetime
import uuid
from asyncio import Lock
from typing import Optional

from html2text import HTML2Text
from sqlalchemy import func, and_, select

from modules import config
from modules.bip21 import bip21_qr_code
from modules.coins import ALL_COINS, CoinNetwork
from modules.electrum_mods.functions import BIP32Node
from modules.exchanges import exchangeRates
from modules.models import Payment, database

invoice_locks = {}


def parse_notes(raw, html) -> dict:
    if html and raw:
        return {"html": html, "raw": raw}
    elif html:
        return {"html": html, "raw": HTML2Text().handle(html)}
    elif raw:
        return {"html": "".join([f"<p>{x}</p>" for x in str(raw).splitlines()]), "raw": raw}
    else:
        return {"html": None, "raw": None}


class TuxPayment:
    def __init__(self):
        self.uuid = str(uuid.uuid4())
        self.creation_date = None
        self.amount_sats = None
        self.last_update = 0
        self.status = "pending"
        self.symbol = None
        self.payment_date = None
        self.invoice_id = None
        self.paid_amount_sats = None
        self.derivation_account = None
        self.derivation_path = None
        self.derivation_index = None
        self.address = None
        self.scripthash = None
        self.qr_code = None
        self.id = None
        self.network: Optional[CoinNetwork] = None

    @classmethod
    async def create(cls, symbol, parent_invoice, amount_sats=None):
        self = TuxPayment()
        self.network = ALL_COINS.get(symbol)
        self.invoice = dict(parent_invoice)
        self.derivation_account = self.network.config("derivation_account", default=0)

        if self.network is None:
            raise ValueError(f"coin '{symbol}' not supported")

        derivation_root = config.xpubs.get(symbol)
        if not derivation_root:
            raise ValueError(f"coin '{symbol}' not set up")

        self.symbol = symbol
        self.invoice_id = parent_invoice['id']

        self.creation_height = await self.network.current_block
        self.creation_date = datetime.datetime.utcnow()
        self.expiry_date = self.creation_date + datetime.timedelta(
            minutes=self.network.config("payment_expiry_min", default=15))

        if amount_sats:
            self.amount_sats = amount_sats
        else:
            self.amount_sats = await exchangeRates.get_exchange_amount(
                to_coin=symbol,
                from_amount=parent_invoice['amount_cents'],
                from_currency=parent_invoice['currency']
            )
        return self

    async def insert(self):
        async with invoice_locks.get(self.symbol, Lock()):
            q = select([func.max(Payment.c.derivation_index).label('idx')]) \
                .where(and_(Payment.c.symbol == self.symbol,
                            Payment.c.derivation_account == self.derivation_account))
            last = await database.fetch_one(q)

            self.derivation_index = 0 if last.idx is None else (last.idx + 1)
            self.derivation_path = f"{self.network.xpub_derivation}/{self.derivation_account}/{self.derivation_index}"
            self.address = self.network.make_address(account=self.derivation_account, index=self.derivation_index)
            self.scripthash = self.network.address_to_scripthash(self.address)
            self.id = await database.execute(Payment.insert().values(**self.sqla_dict()))

            asyncio.create_task(self.network.watch_payment(payment=self.sqla_dict()))

    def sqla_dict(self):
        return {k: v for k, v in self.__dict__.items() if k in [str(x) for x in Payment.c.keys()]}

    def to_dict(self):
        if self.qr_code is None:
            self.qr_code = bip21_qr_code(address=self.address,
                                         amount=self.network.sats_to_coin(self.amount_sats),
                                         label=f"Invoice #{self.invoice_id} payment",
                                         intent=self.network.bip21_intent)

        output = {k: v for k, v in self.__dict__.items() if k != 'network' and not str(k).startswith("_")}
        return output
