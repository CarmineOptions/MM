import asyncio
from decimal import Decimal
from typing import Awaitable, Callable, final
import httpx
from .data_source import DataSource

BINANCE_API_BASE = "https://api.binance.com"
TRADE_ENDPOINT = "/api/v3/aggTrades"


def build_trade_url(base: str, quote: str) -> str:
    symbol = f"{base.upper()}{quote.upper()}"
    return f"{BINANCE_API_BASE}{TRADE_ENDPOINT}?symbol={symbol}&limit=1"


async def fetch_price(base: str, quote: str) -> Decimal:
    """Fetches the latest price of `base/quote` trading pair from Binance.
    The price is fetched using the latest aggregated trade data.
    """
    url = build_trade_url(base, quote)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    resp.raise_for_status()
    data = resp.json()
    return Decimal(data[0]["p"])


async def fetch_cross_price(base: str, quote: str, via: str = "USDT") -> Decimal:
    """
    Fetches the price of `base/quote` via a third currency `via`.
    For example, to get the price of `ETH/USDC`, it fetches `ETH/USDT` and `USDC/USDT`
    and calculates the price as `ETH/USDT / USDC/USDT`.
    """
    base_price, quote_price = await asyncio.gather(
        fetch_price(base, via), fetch_price(quote, via)
    )
    return base_price / quote_price


@final
class BinanceDataSource(DataSource):
    '''
    BinanceDataSource provides price information for trading pairs on Binance.
    It supports fetching prices for specific pairs like ETH/USDC, STRK/USDC, and WBTC/USDC.
    If a pair is not supported, it raises a ValueError.
    '''
    def __init__(self, base: str, quote: str) -> None:
        self.base = base.upper()
        self.quote = quote.upper()
        self._fetcher = self._select_fetcher()

    def _select_fetcher(self) -> Callable[[], Awaitable[Decimal]]:
        match (self.base, self.quote):
            case ("ETH", "USDC"):
                return lambda: fetch_price("ETH", "USDC")
            case ("STRK", "USDC"):
                return lambda: fetch_price("STRK", "USDC")
            case ("WBTC", "USDC"):
                return lambda: fetch_price("BTC", "USDC")
            case _:
                raise ValueError(
                    f"No Binance price fetcher set for `{self.base}/{self.quote}`"
                )

    async def get_price(self) -> Decimal:
        return await self._fetcher()
