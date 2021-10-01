from typing import Dict
from modules import config
from .BTC import BitcoinMainnet, BitcoinTestnet
from .BCH import BitcoinCashMainnet, BitcoinCashTestnet
from .DASH import DashMainnet, DashTestnet
from .LTC import LitecoinMainnet, LitecoinTestnet
from .network import CoinNetwork
from ..logging import logger

ALL_COINS: Dict[str, CoinNetwork] = {}
for x in (BitcoinMainnet, BitcoinCashMainnet, DashMainnet, LitecoinMainnet,
          BitcoinTestnet, BitcoinCashTestnet, DashTestnet, LitecoinTestnet):
    if x.TESTNET and not config.check('debug'):
        continue
    if config.check('enabled', namespace=f"COIN_{x.symbol[1:]}" if x.TESTNET else f"COIN_{x.symbol}"):
        if x.symbol in config.xpubs:
            ALL_COINS[x.symbol] = x
        else:
            logger.warning(f"{x.symbol} is enabled in the configuration, but does not have an xpubkey setup in "
                           f"data/.xpubs.json, add this manually or re-run the setup script")
