from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from MM.instruments.instrument import Instrument, InstrumentAmount
from marketmaking.order import AllOrders, BasicOrder, FutureOrder
from starknet_py.net.client_models import Calls

from marketmaking.waccount import WAccount

@dataclass
class PositionInfo:
    balance_base: Decimal
    balance_quote: Decimal

    withdrawable_base: InstrumentAmount
    withdrawable_quote: InstrumentAmount

    in_orders_base: Decimal
    in_orders_quote: Decimal

    @property
    def total_base(self) -> Decimal:
        return self.balance_base + self.withdrawable_base.amount_hr + self.in_orders_base

    @property
    def total_quote(self) -> Decimal:
        return self.balance_quote + self.withdrawable_quote.amount_hr + self.in_orders_quote

    @staticmethod
    def empty(base_token: Instrument, quote_token: Instrument) -> "PositionInfo":
        return PositionInfo(
            balance_base=Decimal(0),
            balance_quote=Decimal(0),
            withdrawable_base=InstrumentAmount(
                instrument = base_token, 
                amount_raw=0
            ),
            withdrawable_quote=InstrumentAmount(
                instrument=quote_token,
                amount_raw=0
            ),
            in_orders_base=Decimal(0),
            in_orders_quote=Decimal(0),
        )

@dataclass 
class MarketConfig:
    market_id: int
    base_token: Instrument
    quote_token: Instrument


class Market(ABC):
    @property
    @abstractmethod
    def market_cfg(self) -> MarketConfig:
        pass

    @abstractmethod
    async def setup(self, wrapped_account: WAccount) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_current_orders(self) -> AllOrders:
        raise NotImplementedError
    
    @abstractmethod
    def get_submit_order_call(self, order: FutureOrder) -> Calls:
        pass

    @abstractmethod
    def get_close_order_call(self, order: BasicOrder) -> Calls:
        pass

    @abstractmethod
    async def get_total_position(self) -> PositionInfo:
        pass
