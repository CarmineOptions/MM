from dataclasses import dataclass
from decimal import Decimal
import logging

from starknet_py.net.client_models import Calls
import httpx

from MM.marketmaking.order import AllOrders
from MM.oracles.data_sources.data_source import DataSource
from markets.market import MarketABC

@dataclass
class PositionInfo:
    '''
    Represents the position information for a market, including balances, withdrawable amounts, and amounts in orders.
    This class provides properties to calculate the total base and quote amounts of position.
    '''
    balance_base: Decimal
    balance_quote: Decimal

    withdrawable_base: Decimal
    withdrawable_quote: Decimal

    in_orders_base: Decimal
    in_orders_quote: Decimal

    @property
    def total_base(self) -> Decimal:
        return self.balance_base + self.withdrawable_base + self.in_orders_base

    @property
    def total_quote(self) -> Decimal:
        return self.balance_quote + self.withdrawable_quote + self.in_orders_quote

    @staticmethod
    def empty() -> "PositionInfo":
        return PositionInfo(
            balance_base=Decimal(0),
            balance_quote=Decimal(0),
            withdrawable_base= Decimal(0),
            withdrawable_quote = Decimal(0),
            in_orders_base=Decimal(0),
            in_orders_quote=Decimal(0),
        )



@dataclass(frozen=True)
class AccountState:
    position: PositionInfo
    orders: AllOrders

@dataclass
class State:
    account: AccountState
    _fair_price: Decimal

    @property
    def fair_price(self) -> Decimal:
        return self._fair_price

    @fair_price.setter
    def fair_price(self, new_fp: Decimal) -> None:
        logging.info(f"Updating fair price from {self._fair_price} to {new_fp}")
        self._fair_price = new_fp



class PollingStateFetcher:

    def __init__(self, market: MarketABC[Calls | httpx.Request], fair_price_fetcher: DataSource):
        self._market = market
        self._fp_fetcher = fair_price_fetcher


           

