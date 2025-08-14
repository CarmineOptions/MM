import tomli
from .cfg_classes import (
    PriceSourceConfig,
    VenueConfig,
    OrderChainElementConfig,
    ReconcilerConfig,
    StrategyConfig,
    PlatformConfig
)

from .starknet_platform_cfg import StarknetPlatformConfig


class ConfigError(Exception):
    pass


def load_config(path: str) -> StrategyConfig:
    '''
    Loads the strategy configuration from a TOML file.
    '''
    with open(path, "rb") as f:
        raw = tomli.load(f)

    if "platform" not in raw: 
        raise ConfigError("No `platform` config found")

    platform = PlatformConfig(
        name = "starknet",
        config = StarknetPlatformConfig(**raw['platform']['args'])
    )

    if "price_source" not in raw:
        raise ConfigError("No `price_source` config found")
    price = PriceSourceConfig(**raw["price_source"])

    if "market" not in raw:
        raise ConfigError("No `market` config found")
    venue = VenueConfig(**raw['market'])

    if "orderchain" not in raw:
        raise ConfigError("No `orderchain` config found")
    orderchain = [OrderChainElementConfig.from_dict(i) for i in raw["orderchain"]]

    if "reconciler" not in raw:
        raise ConfigError("No `reconciler` config found")
    reconciler = ReconcilerConfig.from_dict(raw["reconciler"])

    cfg = StrategyConfig(
        platform=platform,
        price_source=price, 
        market = venue,
        order_chain=orderchain, 
        reconciler=reconciler,
    )

    return cfg
