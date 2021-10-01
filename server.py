import asyncio

import uvicorn as uvicorn

from modules import config
from modules.application import make_application
from modules.coins import ALL_COINS
from modules.models import database, create_db, Payment
from modules.task_scheduler import instantiate_task_scheduler

app = make_application()


@app.on_event("startup")
async def startup():
    create_db()
    await database.connect()

    for network in ALL_COINS.values():
        asyncio.create_task(network.electrumX.update_peers())

    task_scheduler = await instantiate_task_scheduler()
    task_scheduler.start()
    for payment in await database.fetch_all(Payment.select().where(Payment.c.status.in_(['pending', 'paid']))):
        asyncio.create_task(ALL_COINS[payment['symbol']].watch_payment(payment=dict(payment)))


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


if __name__ == "__main__":
    uvicorn.run(app,
                host="0.0.0.0",
                port=8000,
                debug=config.check("debug"),
                reload=False)
