

# from decimal import Decimal
# from typing import final

# import httpx
# from .data_source import DataSource

#         # "https://api.gateio.ws/api/v4/spot/trades?currency_pair=DOG_USDT&limit=1"
# # BINANCE_BASE_URL = "https://api.binance.com"
# # BINANCE_TRADES_ENDPOINT = "/api/v3/aggTrades"

# GATEIO_BASE_URL = "https://api.gateio.ws/api/v4"
# GATEIO_TRADES_ENDPOINT = "/spot/trades"

# @final
# class GateIoDataSource(DataSource):

#     def __init__(self, base: str, quote: str) -> None:
#         self.base = base
#         self.quote = quote
#         self.url = _binance_trade_url(base, quote)

#     async def get_price(self) -> Decimal:
#         async with httpx.AsyncClient() as client:
#             resp = await client.get(self.url)

#         resp.raise_for_status()
#         data = resp.json()
#         return Decimal(data[0]['p'])


# def _gateio_trade_url(base: str, quote: str) -> str:
#     symbol = (base + '_' + quote).upper()
#     base = GATEIO_BASE_URL + GATEIO_TRADES_ENDPOINT
#     url = base + f'?symbol={symbol}' + '&limit=1'
#     return url


from decimal import Decimal
from typing import Awaitable, Callable, final
import httpx
from .data_source import DataSource

GATEIO_BASE_URL = "https://api.gateio.ws/api/v4"
TRADE_ENDPOINT = "/spot/trades"


def build_trade_url(base: str, quote: str) -> str:
    symbol = f"{base.upper()}_{quote.upper()}"
    return f"{GATEIO_BASE_URL}{TRADE_ENDPOINT}?currency_pair={symbol}&limit=1"

async def fetch_price(base: str, quote: str) -> Decimal:
    url = build_trade_url(base, quote)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    resp.raise_for_status()
    data = resp.json()
    return Decimal(data[0]["price"])

async def fetch_cross_price(base: str, quote: str, via: str = "USDT") -> Decimal:
    base_price = await fetch_price(base, via)
    quote_price = await fetch_price(quote, via)
    return base_price / quote_price


@final
class GateIoDataSource(DataSource):
    def __init__(self, base: str, quote: str) -> None:
        self.base = base.upper()
        self.quote = quote.upper()
        self._fetcher = self._select_fetcher()

    def _select_fetcher(self) -> Callable[[], Awaitable[Decimal]]:
        match (self.base, self.quote):
            case ("WBTC", "DOG"):
                return lambda: fetch_cross_price("WBTC", "DOG")
            case _:
                raise ValueError(f"No Binance price fetcher set for `{self.base}/{self.quote}`")

    async def get_price(self) -> Decimal:
        return await self._fetcher()
