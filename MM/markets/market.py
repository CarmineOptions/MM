from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from instruments.instrument import InstrumentAmount
from marketmaking.order import BasicOrder
from starknet_py.net.client_models import Calls

from MM.marketmaking.waccount import WAccount


# @dataclass
# class UnsettledAmounts:
#     '''
#     Represents the unsettled amounts of base and quote tokens in a market.
#     This is used to track the amounts that are for example matched but not yet settled,
#     and need to be somehow withdrawn or claimed.
#     '''
#     base: InstrumentAmount
#     quote: InstrumentAmount

class Market(ABC):

    @abstractmethod
    def setup(self, wrapped_account: WAccount) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_current_orders(self) -> list[BasicOrder]:
        raise NotImplementedError
    
    @abstractmethod
    async def get_submit_order_call(self) -> Calls:
        pass

    @abstractmethod
    async def get_close_order_call(self, order: BasicOrder) -> Calls:
        pass

    # @abstractmethod
    # def get_unsettled_amounts(self, which: Literal["base", "quote", "both"]) -> UnsettledAmounts:
    #     """
    #     Returns the unsettled amounts of base and quote tokens.
    #     """
    #     raise NotImplementedError
