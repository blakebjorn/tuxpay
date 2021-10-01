import asyncio
import traceback

import requests
from functools import partial

from modules import config
from modules.helpers import to_json
from modules.logging import logger


async def send_webhook(invoice, payment):
    json_body = to_json({
        "invoice": dict(invoice),
        "payment": dict(payment)
    })

    loop = asyncio.get_event_loop()
    for step_back in (60, 600, 3600):
        try:
            resp = await loop.run_in_executor(None, partial(requests.post,
                                                            config.get("payment_callback_url"),
                                                            json=json_body))
            if resp.status_code == 200:
                break
            else:
                logger.warning(f"invoice callback_url returned non-200 status - "
                               f"{resp.status_code} | {resp.text}")
                await asyncio.sleep(step_back)
        except requests.exceptions.RequestException as e:
            logger.warning(f"invoice callback_url request failed:\n{e}")
            logger.debug(f"invoice callback_url request failed:\n{traceback.format_exc()}")
            await asyncio.sleep(step_back)
