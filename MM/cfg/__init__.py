import tomli
from .cfg_classes import StrategyConfig


def load_config(path: str) -> StrategyConfig:
    with open(path, "rb") as f:
        raw = tomli.load(f)
    return StrategyConfig(**raw)
