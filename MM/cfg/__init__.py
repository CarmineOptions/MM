import tomli
from .cfg_classes import (
    AccountConfig,
    AssetConfig,
    OrderChainElementConfig,
    ReconcilerConfig,
    StrategyConfig,
)


class ConfigError(Exception):
    pass


def load_config(path: str) -> StrategyConfig:
    with open(path, "rb") as f:
        raw = tomli.load(f)

    if "account" not in raw:
        raise ConfigError("No `account` config found")
    account = AccountConfig(**raw["account"])

    if "asset" not in raw:
        raise ConfigError("No `asset` config found")
    asset = AssetConfig(**raw["asset"])

    if "orderchain" not in raw:
        raise ConfigError("No `orderchain` config found")
    orderchain = [OrderChainElementConfig.from_dict(i) for i in raw["orderchain"]]

    if "reconciler" not in raw:
        raise ConfigError("No `reconciler` config found")
    reconciler = ReconcilerConfig.from_dict(raw["reconciler"])

    cfg = StrategyConfig(
        account=account, asset=asset, order_chain=orderchain, reconciler=reconciler
    )
    return cfg
