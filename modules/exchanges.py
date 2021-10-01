import datetime
import json
from pathlib import Path
from typing import Dict

import requests

from modules import config
from modules.coins import ALL_COINS
from modules.helpers import age_hours, run_async
from modules.logging import logger


class ExchangeRates:
    def __init__(self):
        exchange_path = Path('data/.cache')
        exchange_path.mkdir(parents=True, exist_ok=True)
        self.fixer_api_key = config.get("fixerio_api_key", namespace="CURRENCY")
        self.fixer_rates = exchange_path / "currencies.json"
        self.coins_file = exchange_path / "coins.json"

        self._currencies = {}
        self._pairs = {}

        if self.fixer_rates.exists():
            self._currencies = json.loads(self.fixer_rates.read_text())
        if self.coins_file.exists():
            self._pairs = json.loads(self.coins_file.read_text())

    @property
    async def coin_rates(self) -> Dict[str, float]:
        if self._pairs.get("timestamp") and age_hours(self._pairs['timestamp']) <= 0.25:
            logger.debug("skipping exchange rate update, less than 15m old")
            return {k: v for k, v in self._pairs.items() if k != 'timestamp'}

        pairs = ",".join({x.kraken for x in ALL_COINS.values()})

        resp = await run_async(requests.get, f'https://api.kraken.com/0/public/Ticker', params={"pair": pairs})
        if resp.status_code != 200:
            logger.error(f"could not update coin values: {resp.text}")
            return self._pairs

        for pair, data in resp.json()['result'].items():
            self._pairs[pair] = (float(data['a'][0]) + float(data['b'][0])) / 2
        self._pairs['timestamp'] = datetime.datetime.now().timestamp()
        self.coins_file.write_text(json.dumps(self._pairs))
        return {k: v for k, v in self._pairs.items() if k != 'timestamp'}

    @property
    async def fixer_io_rates(self):
        rates = {"USD": 1.0}
        if self.fixer_rates.exists():
            rates = json.loads(self.fixer_rates.read_text())
            if age_hours(rates['timestamp']) <= 24:
                return rates

        logger.info("updating FOREX rates")
        symbols = "AUD,CAD,USD,GBP,JPY,EUR,RUB"

        resp = await run_async(requests.get,
                               f'http://data.fixer.io/api/latest?access_key={self.fixer_api_key}'
                               f'&base=EUR&symbols={symbols}')

        if resp.status_code != 200 or "error" in resp.json():
            logger.error(f"could not update forex rates: {resp.text}")
            return rates

        rates = resp.json()['rates']
        usd = float(rates['USD'])
        for x in rates.keys():
            rates[x] /= usd
        rates['USD'] = 1.0
        rates['timestamp'] = datetime.datetime.now().timestamp()
        self.fixer_rates.write_text(json.dumps(rates))
        return rates

    @property
    async def currencies(self):
        if self._currencies.get("timestamp") and age_hours(self._currencies['timestamp']) <= 12:
            logger.debug("skipping exchange rate update, less than 12 hours old")
            return {k: v for k, v in self._currencies.items() if k != 'timestamp'}

        enabled = {x.strip() for x in config.get("enabled_currencies",
                                                 namespace='CURRENCY',
                                                 default='USD').upper().split(",")}

        rates = (await self.fixer_io_rates) if self.fixer_api_key else {"USD": 1.0}

        for k in enabled:
            manual_exchange = config.get(f"{k}_exchange_rate", namespace='CURRENCY')
            if manual_exchange:
                rates[k] = manual_exchange

        self._currencies = {k: v for k, v in rates.items() if k in enabled}
        self._currencies['timestamp'] = datetime.datetime.now().timestamp()
        return {k: v for k, v in self._currencies.items() if k != 'timestamp'}

    async def get_exchange_amount(self, to_coin, from_amount, from_currency):
        """
        convert fiat amount (in dollars) to satoshis
        """
        # Get USD rate
        if from_currency != "USD":
            from_amount = from_amount / (await self.currencies)[from_currency]

        # Get Coin rate
        network = ALL_COINS[to_coin]
        exchange = (await self.coin_rates)[network.kraken]
        return int(round(from_amount / exchange * (10 ** network.decimals) / 100))

    async def get_reverse_exchange_amount(self, from_amount, from_coin, to_currency):
        """
        Convert satoshis to fiat denomination (in dollars)
        """

        network = ALL_COINS[from_coin]
        coin_exchange = (await self.coin_rates)[network.kraken]
        fiat_rate = network.sats_to_coin(from_amount) * coin_exchange

        if to_currency != "USD":
            forex = (await self.currencies)[to_currency]
            return fiat_rate * forex
        return fiat_rate


exchangeRates = ExchangeRates()
