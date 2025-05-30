import os
from decimal import Decimal

from pydantic import BaseModel
import tomli


class AccountConfig(BaseModel):
    rpc_url_env: str
    wallet_address_env: str
    account_password_env: str
    keystore_path_env: str

    @property
    def rpc_url(self) -> str | None:
        return os.environ.get(self.rpc_url_env)

    @property
    def wallet_address(self) -> str | None:
        return os.environ.get(self.wallet_address_env)
    
    @property
    def account_password(self) -> str | None:
        return os.environ.get(self.account_password_env)

    @property
    def keystore_path(self) -> str | None:
        return os.environ.get(self.keystore_path_env)


class AssetConfig(BaseModel):
    base_asset: str
    quote_asset: str

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
