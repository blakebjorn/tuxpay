import asyncio

import aiohttp

from modules import config
from modules.helpers import to_json
from modules.logging import logger


async def send_webhook(invoice, payment):
    json_body = to_json({
        "invoice": dict(invoice),
        "payment": dict(payment)
    })

    for step_back in (60, 600, 3600):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(config.get("payment_callback_url"), json=json_body) as resp:
                    if resp.status == 200:
                        break
                    else:
                        logger.warning(f"invoice callback_url returned non-200 status - "
                                       f"{resp.status} | {resp.text}")
                        await asyncio.sleep(step_back)
        except aiohttp.ClientError as e:
            logger.error(f"invoice callback_url request failed", exc_info=e)
            await asyncio.sleep(step_back)
