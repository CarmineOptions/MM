from typing import Callable
import requests


SOURCE_DATA = {
    1: 'https://data-api.binance.vision/api/v3/aggTrades?symbol=ETHUSDC',
    2: 'https://data-api.binance.vision/api/v3/aggTrades?symbol=STRKUSDC',
    3: 'https://data-api.binance.vision/api/v3/aggTrades?symbol=BTCUSDC',
}

def fetch_price_from_url(url: str) -> float:
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    if not data:
        raise ValueError("No data returned from API")
    return float(sorted(data, key = lambda x: x['T'])[-1]['p'])  

# Default processors for simple markets that don't need to process price 
# in any way
def simple_fetcher(url: str) -> Callable[[], float]:
    return lambda: fetch_price_from_url(url)


def wbtc_dog_price_fetcher() -> float:
    btc_price = fetch_price_from_url('https://data-api.binance.vision/api/v3/aggTrades?symbol=BTCUSDC')
    dog_price = requests.get('https://api.gateio.ws/api/v4/spot/trades?currency_pair=DOG_USDT&limit=1')
    dog_price = float(dog_price.json()[0]['price'])

    return dog_price / btc_price


PRICE_FETCHERS: dict[int, Callable[[], float]] = {
    1: simple_fetcher(SOURCE_DATA[1]),
    2: simple_fetcher(SOURCE_DATA[2]),
    3: simple_fetcher(SOURCE_DATA[3]),
    11: wbtc_dog_price_fetcher
}


def get_price_fetcher(market_id: int) -> Callable[[], float]:
    fetcher = PRICE_FETCHERS.get(market_id)
    if not fetcher:
        raise ValueError(f"No processor found for market_id {market_id}")
    return fetcher


if __name__ == '__main__':
    wbtc_dog_price_fetcher()
