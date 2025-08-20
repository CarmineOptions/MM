
from markets.market import StarknetMarketABC

from .bundling_tx_builder import BundlingTransactionBuilder
from .sequential_tx_builder import SequentialTransactionBuilder
from .tx_builder import TxBuilder


def get_tx_builder(name: str, market: StarknetMarketABC) -> TxBuilder:
    if name == 'bundling_tx_builder':
        return BundlingTransactionBuilder(market=market)
    if name == 'sequential_tx_builder':
        return SequentialTransactionBuilder(market=market)

    raise ValueError(f"Unknown tx builder provided: `{name}`")