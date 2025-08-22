from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

import httpx

from instruments.instrument import Instrument, InstrumentAmount
from marketmaking.order import AllOrders, BasicOrder, FutureOrder
from starknet_py.net.client_models import Calls

if TYPE_CHECKING:
    from state.state import State

@dataclass
class PositionInfo:
    '''
    Represents the position information for a market, including balances, withdrawable amounts, and amounts in orders.
    This class provides properties to calculate the total base and quote amounts of position.
    '''
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
    """ 
    Represents the configuration for a market, including its ID, base token, and quote token.
    The `market_id` doesn't neccessarily matches the ID of the market on the exchange,
    or isn't necessarily unique in the context of the strategy but it is used to identify
    the market of some venue in the context of the strategy. 
    (So basically the ids are unique per venue)
    """
    market_id: int
    base_token: Instrument
    quote_token: Instrument


@dataclass
class PrologueOp_SeekLiquidity:
    amount: Decimal

#  Once there are more Ops, this wil become an Union
PrologueOps = PrologueOp_SeekLiquidity 


class MarketABC[T](ABC):
    '''
    Abstract base class for a market in the market making strategy.
    This class defines the interface for interacting with a market, including methods for
    setting up the market, retrieving current orders, submitting and closing orders,
    withdrawing funds, and getting total position information.
    '''
    @property
    @abstractmethod
    def market_cfg(self) -> MarketConfig:
        '''
        Returns the configuration of the market.
        '''
        pass

    @abstractmethod
    async def setup(self) -> None:
        '''
        Sets up trading on the market.
        This method is called to initialize the market with necessary configurations and account details.
        Eg. in case of Remus, it approves the tokens for trading.

        This should be run before the actual trading starts.
        '''
        raise NotImplementedError

    @abstractmethod
    async def get_current_orders(self) -> AllOrders:
        '''
        Retrieves the current orders on the market.
        '''
        raise NotImplementedError
    
    @abstractmethod
    def get_submit_order_call(self, order: FutureOrder) -> T:
        '''
        Returns the call to submit an order to the market. The call
        itself is then executed outside of the market class.
        '''
        raise NotImplementedError

    @abstractmethod
    def get_close_order_call(self, order: BasicOrder) -> T:
        '''
        Returns the call to cancel an order. The call
        itself is then executed outside of the market class.
        '''
        raise NotImplementedError

    # @abstractmethod
    # def get_withdraw_call(self, state: "State", amount: InstrumentAmount) -> T:
    #     '''
    #     Returns the call to withdraw any pending/matched funds. The call
    #     itself is then executed outside of the market class.
    #     '''
    #     raise NotImplementedError

    @abstractmethod
    async def get_total_position(self) -> PositionInfo:
        '''
        Returns the total position for the market.
        '''
        raise NotImplementedError

    # @abstractmethod
    # def seek_additional_liquidity(self, state: "State") -> T:
    #     """
    #     Function used for getting additional liquidity that is locked somewhere.

    #     eg. In case of Remus this produces a claim call.
    #     """
    #     raise NotImplementedError
    
    @abstractmethod
    def prologue_ops_to_calls(self, state: "State", ops: list[PrologueOps]) -> list[T]:
        """
        Function used for converting Prologue 
        """
        raise NotImplementedError


class StarknetMarketABC(MarketABC[Calls]):
    pass

class OffchainMarketABC(MarketABC[httpx.Request]):
    pass
