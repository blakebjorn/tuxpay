import asyncio
import datetime
import json
import warnings
from pathlib import Path
from typing import Tuple, Optional, TYPE_CHECKING

import aiorpcx

from modules import config
from modules.electrum_mods.functions import BIP32Node, pubkey_to_address, address_to_script, \
    script_to_scripthash, constants
from modules.electrumx import ElectrumX, ElectrumError
from modules.helpers import inv_dict, timestamp
from modules.logging import logger
from modules.models import database, Payment, Invoice
from modules.webhooks import send_webhook

if TYPE_CHECKING:
    from modules.electrum_mods import PartialTransaction


class CoinNetwork(constants.AbstractNet):
    symbol = ""
    name = ""
    segwit = True
    address_format = "p2wpkh"
    bip21_intent = "bitcoin:"

    kraken = ""
    electrumX = None
    decimals = 8
    watched_payments = {}

    TESTNET = False
    SIGHASH_FLAG = 0x00000001
    TX_VERSION = 2

    XPRV_HEADERS = {}
    XPUB_HEADERS = {}
    WIF_PREFIX = None
    BIP44_COIN_TYPE = -1
    PEER_DEFAULT_PORTS = {'t': 50001, 's': 50002}

    def __init__(self):
        self.electrumX = ElectrumX(self.symbol, default_ports=self.PEER_DEFAULT_PORTS)
        self.XPRV_HEADERS_INV = inv_dict(self.XPRV_HEADERS)
        self.XPUB_HEADERS_INV = inv_dict(self.XPUB_HEADERS)

        self._block_queue = None
        self._block_lock = None
        self._relayfee: Optional[Tuple[int, float]] = None
        self._current_block: Optional[int] = None
        self._current_feerate: Optional[Tuple[int, float]] = None
        self._svg_icon = None

        xpub = config.xpubs.get(self.symbol)
        if xpub is None:
            warnings.warn(f"No xPub added for {self.symbol} - address generation disabled")
            self.xpub_node = None
            self.xpub_derivation = None
        else:
            self.xpub_node = BIP32Node.from_xkey(xpub['xpub'], net=self)
            self.xpub_derivation = xpub['derivation_path']

    @property
    def icon(self):
        if self._svg_icon is not None:
            return self._svg_icon
        filename = Path(__file__).parent / 'icons' / f"{self.symbol[1:] if self.TESTNET else self.symbol}.svg"
        if filename.exists():
            self._svg_icon = filename.read_text()
        else:
            self._svg_icon = ""
        return self._svg_icon

    @property
    def icon_b64(self):
        return self._svg_icon

    def sats_to_coin(self, sats: Optional[int]) -> Optional[float]:
        if sats is None:
            return None
        return round(sats * 10 ** -self.decimals, self.decimals)

    def coin_to_sats(self, amt):
        return int(round(amt * 10 ** self.decimals))

    @property
    def root_symbol(self):
        if self.TESTNET:
            return self.symbol[1:]
        return self.symbol

    @property
    def default_xpub_derivation_path(self):
        return "/".join(['84h' if self.segwit else '44h',
                         '1h' if self.TESTNET else f"{self.BIP44_COIN_TYPE}h",
                         '0h'])

    @property
    async def relay_fee(self):
        res = await self.electrum_call(ElectrumX.blockchain_relayfee, [])
        assert res > 0
        # check response
        relay_fee = int(res * 10 ** self.decimals)
        relay_fee = max(0, relay_fee)
        return relay_fee

    @property
    async def current_block(self):
        if self._block_lock is None:
            self._block_lock = asyncio.Lock()

        async with self._block_lock:
            if self._current_block is not None:
                return self._current_block

            self._block_queue = asyncio.Queue()
            ret = await self.electrumX.call(ElectrumX.blockchain_headers_subscribe, [], self._block_queue)
            self._current_block = int(ret[0]['height'])
        asyncio.create_task(self.watch_blocks())
        return self._current_block

    async def watch_blocks(self):
        while True:
            ret = await self._block_queue.get()
            try:
                self.electrumX.validate_elextrumx_call(ElectrumX.blockchain_headers_subscribe, ret)
            except ElectrumError:
                await self.electrumX.penalize_server()
                continue
            logger.info(f"{self.symbol} - new block @ {ret[0]['height']}")
            self._current_block = int(ret[0]['height'])

    @property
    async def current_feerate(self):
        # Cached feerate
        if self._current_feerate is not None and self._current_feerate[0] == (await self.current_block):
            return self._current_feerate[1]

        fee_estimate = await self.electrum_call(ElectrumX.blockchain_estimatefee, [1])
        if fee_estimate and fee_estimate > 0:
            # Convert to sat/byte
            fee_estimate /= 1024
            fee_estimate *= 10 ** self.decimals
        else:
            # Fallback to coin default
            fee_estimate = float(self.config('fallback_feerate'))
        return fee_estimate

    def config(self, key, default=None):
        """
        Shorthand to get config entries for the parent coin, equivalent to `modules.config.get(key, coin=self.symbol)`
        """
        return config.get(key, coin=self.symbol, default=default)

    async def get_transactions(self, script_hash, ignored_tx_hashes=None):
        transactions = {}
        history = await self.electrum_call(ElectrumX.blockchain_scripthash_get_history, [script_hash])
        for tx in history:
            tx_hash = tx.get("tx_hash")
            if ignored_tx_hashes and tx_hash in ignored_tx_hashes:
                continue
            transactions[tx_hash] = await self.electrum_call(ElectrumX.blockchain_transaction_get, [tx_hash, True])
            if 'fee' in tx:
                transactions[tx_hash]['mempool_fee'] = tx['fee']
        return transactions

    async def watch_payment(self, payment: dict):
        logger.info(f"Watching payment {payment['uuid']}")

        queue = asyncio.Queue()
        self.watched_payments[payment['uuid']] = payment
        original_payment = payment.copy()

        first_loop = True
        awaiting_mempool = True
        awaiting_confirmations = True
        current_block = await self.current_block
        script_hash = payment['scripthash']
        ignored_tx_hashes = set()

        while True:
            if awaiting_mempool:
                if first_loop:
                    first_loop = False
                    logger.info(f"Subscribing to scripthash")
                    await self.electrum_call(ElectrumX.blockchain_scripthash_subscribe, [script_hash], queue)
                else:
                    logger.info(f"Waiting for scripthash changes")
                    await queue.get()
                    logger.info(f"Done waiting")
            elif awaiting_confirmations:
                logger.info("waiting for new block")
                while current_block == await self.current_block:
                    await asyncio.sleep(1)
                current_block = await self.current_block
            else:
                logger.info(f"Finished watching payment {payment['uuid']}")
                break

            logger.info(f"Payment Update: {payment['uuid']} - {script_hash}")
            all_transactions = await self.get_transactions(script_hash, ignored_tx_hashes=ignored_tx_hashes)

            # Check if "received"
            valid_tx = []
            for x in all_transactions.values():
                if 'time' not in x:
                    valid_tx.append(x)
                elif datetime.datetime.utcfromtimestamp(x.get('time', 0) or 0) > payment['creation_date']:
                    valid_tx.append(x)
                else:
                    ignored_tx_hashes.add(x.get("tx_hash"))

            payment['transactions'] = valid_tx

            mempool_sats = 0
            chain_sats = 0
            confirmed_sats = 0
            req_confirmations = int(self.config('required_confirmations', default=6))
            for tx in valid_tx:
                for vout in tx['vout']:
                    for addr in vout['scriptPubKey']['addresses']:
                        if addr == payment['address']:
                            sats = int(round(vout['value'] * 10 ** self.decimals))
                            mempool_sats += sats
                            confirmations = tx.get("confirmations", 0)

                            # If instantsend lock is present, treat as if 1 confirmation
                            if confirmations == 0 and tx.get("instantlock"):
                                warnings.warn("test instantlock")
                                confirmations = 1

                            if confirmations > 0 or req_confirmations == 0:
                                chain_sats += sats

                            if confirmations >= req_confirmations:
                                if req_confirmations == 0 and confirmations == 0:
                                    warnings.warn("Check zeroconf fees")
                                    # CHECK IF mempool_fee is greater than the coins current next-block feerate
                                    mempool_fee = tx.get("mempool_fee")
                                    # If ElectrumX doesn't return this it will need to get calculated manually
                                confirmed_sats += sats

            if datetime.datetime.utcnow() > payment['expiry_date'] and payment['status'] == "pending":
                payment['status'] = "expired"
                payment['last_update'] = timestamp()
                awaiting_confirmations = False
            else:
                if confirmed_sats >= payment['amount_sats']:
                    awaiting_confirmations = False
                    if payment['status'] != "confirmed":
                        payment['status'] = "confirmed"
                        payment['payment_date'] = payment['payment_date'] or datetime.datetime.utcnow()
                        payment['paid_amount_sats'] = payment['paid_amount_sats'] or mempool_sats
                        payment['last_update'] = timestamp()

                if mempool_sats >= payment['amount_sats']:
                    if payment['status'] == 'pending':
                        payment['status'] = 'paid'
                        payment['payment_date'] = payment['payment_date'] or datetime.datetime.utcnow()
                        payment['paid_amount_sats'] = payment['paid_amount_sats'] or mempool_sats
                        payment['last_update'] = timestamp()

            if awaiting_mempool:
                if payment['status'] in ('expired', 'confirmed') or chain_sats > payment['amount_sats']:
                    awaiting_mempool = False
                    await self.unsubscribe_electrumx("blockchain.scripthash.unsubscribe",
                                                     [payment['scripthash']], queue)

            changes = {k: payment[k] for k, v in original_payment.items() if v != payment[k] and k != "transactions"}
            if (tx_serialized := json.dumps(valid_tx)) != original_payment.get('transactions'):
                changes['transactions'] = tx_serialized

            if changes:
                await database.execute(Payment.update()
                                       .where(Payment.c.id == payment['id'])
                                       .values(**changes))

                # If the payment changes, the invoice should as well, calculate the invoice status now
                invoice = await database.fetch_one(Invoice.select().where(Invoice.c.id == payment['invoice_id']))
                invoice = dict(invoice)
                original_invoice = invoice.copy()

                if payment['status'] == 'confirmed' and invoice['status'] in ('pending', 'paid'):
                    invoice['status'] = "confirmed"
                elif payment['status'] == 'paid' and invoice['status'] == 'pending':
                    invoice['status'] = "paid"

                if invoice['status'] != original_invoice['status']:
                    if config.get("payment_callback_url"):
                        asyncio.create_task(send_webhook(invoice, payment))
                    await database.execute(Invoice.update().where(Invoice.c.id == invoice['id']).values(
                        **{"status": invoice['status'], "payment_date": payment['payment_date']}))

                if invoice['status'] == 'confirmed':
                    if config.check("email_notifications", namespace="EMAIL"):
                        from modules.email import email_invoice
                        asyncio.create_task(email_invoice(invoice))

            self.watched_payments[payment['uuid']] = payment

    def make_address(self, xpub_node: BIP32Node = None, account=0, index=0) -> str:
        assert isinstance(index, int) and index >= 0
        assert isinstance(account, int) and account >= 0
        xpub_node = xpub_node or self.xpub_node

        subkey = xpub_node.subkey_at_public_derivation(f"/{account}/{index}")
        pubkey = subkey.eckey.get_public_key_bytes(compressed=True).hex()
        return pubkey_to_address(self.address_format, pubkey, net=self)

    def address_to_script(self, address):
        return address_to_script(address, net=self)

    def address_to_scripthash(self, address):
        script = self.address_to_script(address)
        return script_to_scripthash(script)

    async def electrum_call(self, method, params=None, queue=None):
        return await self.electrumX.call(method, params, queue=queue)

    async def unsubscribe_electrumx(self, method, params=None, queue=None):
        assert queue is not None
        logger.info(f"Unsubscribing from {method} {params}")
        await self.electrumX.get_session()
        try:
            await self.electrumX.session.send_request(method, params)
        except aiorpcx.RPCError:
            # not all servers implement this
            pass
        self.electrumX.unsubscribe(queue)

    def estimate_tx_size(self, tx: 'PartialTransaction'):
        return tx.estimated_size(self)
