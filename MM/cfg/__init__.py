import tomli
from .cfg_classes import (
    AccountConfig,
    PriceSourceConfig,
    VenueConfig,
    OrderChainElementConfig,
    ReconcilerConfig,
    StrategyConfig,
    TxBuilderConfig
)


class ConfigError(Exception):
    pass


def load_config(path: str) -> StrategyConfig:
    '''
    Loads the strategy configuration from a TOML file.
    '''
    with open(path, "rb") as f:
        raw = tomli.load(f)

    if "account" not in raw:
        raise ConfigError("No `account` config found")
    account = AccountConfig(**raw["account"])

    if "price_source" not in raw:
        raise ConfigError("No `price_source` config found")
    price = PriceSourceConfig(**raw["price_source"])

    if "market" not in raw:
        raise ConfigError("No `market` config found")
    venue = VenueConfig(**raw['market'])

    if 'tx_builder' not in raw: 
        raise ConfigError('No `tx_builder` config found')
    tx_builder = TxBuilderConfig(**raw['tx_builder'])

    if "orderchain" not in raw:
        raise ConfigError("No `orderchain` config found")
    orderchain = [OrderChainElementConfig.from_dict(i) for i in raw["orderchain"]]

    if "reconciler" not in raw:
        raise ConfigError("No `reconciler` config found")
    reconciler = ReconcilerConfig.from_dict(raw["reconciler"])

    cfg = StrategyConfig(
        account=account, 
        price_source=price, 
        market = venue,
        order_chain=orderchain, 
        reconciler=reconciler,
        tx_builder=tx_builder
    )
    return cfg
