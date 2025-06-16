from .data_source import DataSource
from .binance import BinanceDataSource
from .gateio import GateIoDataSource


def get_data_source(source: str, base: str, quote: str) -> DataSource:
    if source.lower() == "binance":
        return BinanceDataSource(base=base, quote=quote)
    elif source.lower() == "gateio":
        return GateIoDataSource(base=base, quote=quote)
    else:
        raise ValueError(f"Unknown data source `{source}` provided")
