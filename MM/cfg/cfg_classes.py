from decimal import Decimal

from pydantic import BaseModel

from .starknet_platform_cfg import StarknetPlatformConfig

class VenueConfig(BaseModel):
    '''
    Holds the configuration for the trading venue.
    '''
    venue: str
    market_id: int

class PriceSourceConfig(BaseModel):
    '''
    Holds the configuration for the price source.
    '''
    base_asset: str
    quote_asset: str
    price_source: str


class OrderChainElementConfig(BaseModel):
    '''
    Holds the configuration for an element in the order chain.
    '''
    name: str
    args: dict[str, Decimal | int]

    @staticmethod
    def from_dict(d: dict[str, int | Decimal]) -> "OrderChainElementConfig":
        name = d["name"]
        del d["name"]
        return OrderChainElementConfig(name=str(name), args=d)


class ReconcilerConfig(BaseModel):
    '''
    Holds the configuration for the Reconciler.
    '''
    name: str
    args: dict[str, Decimal | int]

    @staticmethod
    def from_dict(d: dict[str, int | Decimal]) -> "ReconcilerConfig":
        name = d["name"]
        del d["name"]
        return ReconcilerConfig(name=str(name), args=d)


class PlatformConfig(BaseModel):
    name: str
    config: StarknetPlatformConfig

class StrategyConfig(BaseModel):
    '''
    Holds the configuration for the trading strategy.
    '''
    platform: PlatformConfig
    market: VenueConfig
    price_source: PriceSourceConfig
    order_chain: list[OrderChainElementConfig]
    reconciler: ReconcilerConfig
