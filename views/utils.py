import asyncio
import base64
from typing import List, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from modules.coins import ALL_COINS
from modules.exchanges import exchangeRates
from modules.helpers import JSONResponse

router = APIRouter(prefix='/api')


async def get_coins_raw():
    symbols = list(ALL_COINS.keys())
    fee_rates = await asyncio.gather(*[ALL_COINS[x].current_feerate for x in symbols])
    fee_dict = {symbol: fee_rates[i] for i, symbol in enumerate(symbols)}
    return [{
        "symbol": x.symbol,
        "name": x.name,
        "decimals": x.decimals,
        "fee_rate": fee_dict[x.symbol],
        "fee_estimate": await exchangeRates.get_reverse_exchange_amount(
            fee_dict[x.symbol] * (372 if x.segwit else 374),  # 1 input 2 output
            x.symbol,
            'USD'
        ),
        "icon": base64.b64encode(x.icon.encode())
    } for x in ALL_COINS.values()]


class CoinResponse(BaseModel):
    symbol: str = Field(title="Symbol used to reference the coin", example="BTC")
    name: str = Field(title="Name of the coin", example="Bitcoin")
    decimals: int = Field(title="Decimal places representing the smallest denomination (1 Satoshi)", example=8)
    fee_rate: int = Field(title="Current feerate (in sats/byte)", example=1)
    fee_estimate: float = Field(title="Estimated fee (in USD) of a transaction (1 input, 2 outputs)", example=0.13)
    icon: str = Field(title="Base64 encoded SVG icon corresponding to the coin",
                      example=base64.b64encode(b"<svg></svg>"))


class CoinsResponse(BaseModel):
    currencies: Dict[str, float] = Field(title="Fiat exchange rates (USD -> X)",
                                         example={"USD": 1.0, "CAD": 1.31})
    coins: List[CoinResponse]


@router.get('/coins', response_model=CoinsResponse, tags=['invoice', 'payment'])
async def get_coins():
    """
    Returns an array of data pertaining to all the payment types supported by the server
    """
    return JSONResponse({
        "coins": await get_coins_raw(),
        "currencies": await exchangeRates.currencies
    })
