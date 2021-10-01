import asyncio
import json

from fastapi import APIRouter
from starlette.websockets import WebSocketDisconnect
from websockets import ConnectionClosed

from modules.bip21 import bip21_qr_code
from modules.coins import ALL_COINS
from modules.helpers import to_json, JSONResponse, NOT_FOUND
from modules.logging import logger
from modules.models import Payment, database, Invoice
from views.api_models import PaymentCustomerReadModel

router = APIRouter(prefix='/api')


@router.get('/payment', response_model=PaymentCustomerReadModel, tags=['payment'])
async def payment_get(uuid: str):
    ret = await database.fetch_one(Payment.select().where(Payment.c.uuid == uuid))
    if ret:
        inv = await database.fetch_one(Invoice.select().where(Invoice.c.id == ret['invoice_id']))
        ret = dict(ret)
        ret['amount_coin'] = ALL_COINS[ret['symbol']].sats_to_coin(ret['amount_sats'])
        ret['paid_amount_coin'] = ALL_COINS[ret['symbol']].sats_to_coin(ret['paid_amount_sats'])
        ret['qr_code'] = bip21_qr_code(address=ret['address'],
                                       amount=ret['amount_coin'],
                                       label=f"Payment #{ret['uuid']}",
                                       intent=ALL_COINS[ret['symbol']].bip21_intent)
        ret['invoice'] = inv
        return JSONResponse({"payment": ret})
    else:
        return NOT_FOUND


async def watch_payment(websocket):
    await websocket.accept()
    try:
        msg = await websocket.receive_text()
        try:
            dat = json.loads(msg)
        except ValueError:
            await websocket.send_text(to_json({"error": "invalid request"}))
            logger.info("Closing websocket - bad request")
            return await websocket.close()

        uuid_ = dat.get("uuid")
        payment: Payment = await database.fetch_one(Payment.select().where(Payment.c.uuid == uuid_))
        if payment is None:
            await websocket.send_text(to_json({"error": "not found"}))
            logger.info("Closing websocket - payment not found")
            return await websocket.close()

        payment = dict(payment)
        network = ALL_COINS[payment['symbol']]

        if payment['uuid'] not in network.watched_payments:
            asyncio.create_task(network.watch_payment(payment))
            await asyncio.sleep(0.01)
            while payment['uuid'] not in network.watched_payments:
                logger.info("waiting for watcher to instantiate")
                await asyncio.sleep(0.1)

        last_update = 0
        while True:
            ret = network.watched_payments[payment['uuid']]
            if ret['last_update'] > last_update:
                last_update = int(ret['last_update'])
                await websocket.send_text(to_json({
                    "status": ret["status"],
                    "transactions": ret.get('transactions', [])
                }))

            if ret['status'] == 'expired' or ret['status'] == 'confirmed':
                break

            await asyncio.sleep(0.01)
        await websocket.close()
    except (ConnectionClosed, WebSocketDisconnect) as e:
        pass
