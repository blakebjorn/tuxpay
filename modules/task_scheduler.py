import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from modules.electrum_mods.tux_mods import sweep, BIP32Node, PartialTransaction, serialize_privkey, NetworkLock
from modules import config
from modules.coins import ALL_COINS
from modules.credentials import CredentialManager
from modules.electrumx import ElectrumX
from modules.logging import logger
from modules.models import database, Payment


def _await(promise):
    return asyncio.get_event_loop().run_until_complete(promise)


async def update_electrumx_peers():
    await asyncio.gather(*[coin.electrumX.update_peers() for coin in ALL_COINS.values()])


async def sweep_wallet(symbol, address, max_fee_rate, max_fee_prop, decryption_password=None):
    logger.info(f"{symbol} - beginning sweep")

    try:
        seed = CredentialManager.get_seed(decryption_password=decryption_password)
    except ValueError as e:
        logger.error(f"{symbol} - could not sweep, hot wallet credentials are not all available: {e}")
        return

    node = BIP32Node.from_rootseed(seed, xtype='standard')
    network = ALL_COINS[symbol]
    res = await database.fetch_all(Payment.select().where(Payment.c.symbol == symbol))

    private_keys = []
    for inv in res:
        priv: BIP32Node = node.subkey_at_private_derivation(inv['derivation_path'])
        private_keys.append(serialize_privkey(priv.eckey.get_secret_bytes(),
                                              True, network.address_format, net=network))

    try:
        tx, key_pairs = await sweep(privkeys=private_keys,
                                    net=network,
                                    to_address=address)
        tx: PartialTransaction
    except ValueError as e:
        logger.error(f"{symbol} - Could not sweep - {e}")
        return

    # PartialTransaction will prefix addresses with bc1 regardless of network, so we must compare the script pubkeys
    recipient_script = network.address_to_script(address)

    if len(tx.inputs()) == 1 and tx.inputs()[0].scriptpubkey.hex() == recipient_script:
        logger.info(f"{symbol} - No funds exist outside of sweep address, no action will be taken")
        return

    transfer_value = sum(
        (x.value_sats() for x in tx.inputs() if x.scriptpubkey.hex() != recipient_script)) - tx.get_fee()
    if tx.get_fee() > (transfer_value * max_fee_prop):
        logger.info(f"{symbol} - Fees exceed {max_fee_prop * 100}% of transaction value "
                    f"({tx.get_fee()} vs. {transfer_value})")
        return

    with NetworkLock(network):
        fee_rate = tx.get_fee() / tx.estimated_size(network)
        if fee_rate > max_fee_rate:
            logger.info(f"{symbol} - Fee rate exceeds max allowed value ({fee_rate} vs. {max_fee_rate})")
            return

        tx.sign(keypairs=key_pairs, net=network)
        raw_tx = tx.serialize()

        logger.info(f"{symbol} Sweep - "
                    f"Inputs: {[(inp.address, inp.value_sats()) for inp in tx.inputs()]} - "
                    f"Outputs: {[(out.address, out.value) for out in tx.outputs()]}")

    await network.electrum_call(ElectrumX.blockchain_transaction_broadcast, [raw_tx])


async def instantiate_task_scheduler():
    scheduler = AsyncIOScheduler()

    # Add sweep jobs
    for symbol, coin in ALL_COINS.items():
        if (addr := config.get("sweep_address", coin=symbol)) and \
                (cron := config.get("sweep_cron_string", coin=symbol)):
            scheduler.add_job(sweep_wallet,
                              CronTrigger.from_crontab(cron),
                              args=[
                                  symbol, addr,
                                  float(config.get("sweep_max_fee_rate", coin=symbol)),
                                  float(config.get("sweep_max_fee_prop", coin=symbol))
                              ])

    return scheduler
