import os
from decimal import Decimal

from pydantic import BaseModel


class AccountConfig(BaseModel):
    rpc_url_env: str
    wallet_address_env: str
    password_path_env: str
    keystore_path_env: str

    @property
    def rpc_url(self) -> str | None:
        return os.environ.get(self.rpc_url_env)

    @property
    def wallet_address(self) -> str | None:
        return os.environ.get(self.wallet_address_env)

    @property
    def keystore_path(self) -> str | None:
        return os.environ.get(self.keystore_path_env)

    @property
    def password(self) -> str | None:
        path = os.environ.get(self.password_path_env)
        if path is None:
            return None

        with open(path, "r") as f:
            pwd = f.read().strip()

        return pwd


class AssetConfig(BaseModel):
    base_asset: str
    quote_asset: str
    market_id: int
    price_source: str


class MarketMakerConfig(BaseModel):
    target_relative_distance_from_FP: Decimal
    max_relative_distance_from_FP: Decimal
    min_relative_distance_from_FP: Decimal

    order_size: Decimal
    minimal_remaining_size: Decimal
    max_orders_per_side: int


class StrategyConfig(BaseModel):
    account: AccountConfig
    asset: AssetConfig
    marketmaker: MarketMakerConfig
