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

class VenueConfig(BaseModel):
    venue: str
    market_id: int

class PriceSourceConfig(BaseModel):
    base_asset: str
    quote_asset: str
    price_source: str


class OrderChainElementConfig(BaseModel):
    name: str
    args: dict[str, Decimal | int]

    @staticmethod
    def from_dict(d: dict[str, int | Decimal]) -> "OrderChainElementConfig":
        name = d["name"]
        del d["name"]
        return OrderChainElementConfig(name=str(name), args=d)


class ReconcilerConfig(BaseModel):
    name: str
    args: dict[str, Decimal | int]

    @staticmethod
    def from_dict(d: dict[str, int | Decimal]) -> "ReconcilerConfig":
        name = d["name"]
        del d["name"]
        return ReconcilerConfig(name=str(name), args=d)


class StrategyConfig(BaseModel):
    account: AccountConfig
    market: VenueConfig
    price_source: PriceSourceConfig
    order_chain: list[OrderChainElementConfig]
    reconciler: ReconcilerConfig
