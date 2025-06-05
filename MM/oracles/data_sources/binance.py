
from decimal import Decimal
from typing import Awaitable, Callable, final
import httpx
from .data_source import DataSource

BINANCE_API_BASE  = "https://api.binance.com"
TRADE_ENDPOINT = "/api/v3/aggTrades"


def build_trade_url(base: str, quote: str) -> str:
    symbol = f"{base.upper()}{quote.upper()}"
    return f"{BINANCE_API_BASE}{TRADE_ENDPOINT}?symbol={symbol}&limit=1"

async def fetch_price(base: str, quote: str) -> Decimal:
    url = build_trade_url(base, quote)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    resp.raise_for_status()
    data = resp.json()
    return Decimal(data[0]["p"])

async def fetch_cross_price(base: str, quote: str, via: str = "USDT") -> Decimal:
    base_price = await fetch_price(base, via)
    quote_price = await fetch_price(quote, via)
    return base_price / quote_price


@final
class BinanceDataSource(DataSource):
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
                raise ValueError(f"No Binance price fetcher set for `{self.base}/{self.quote}`")

    async def get_price(self) -> Decimal:
        return await self._fetcher()
