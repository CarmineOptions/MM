from abc import ABC, abstractmethod

from marketmaking.market import PositionInfo
from marketmaking.order import AllOrders, BasicOrder, FutureOrder
from starknet_py.net.client_models import Calls

from marketmaking.waccount import WAccount


class Market(ABC):

    @abstractmethod
    async def setup(self, wrapped_account: WAccount) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_current_orders(self) -> AllOrders:
        raise NotImplementedError
    
    @abstractmethod
    async def get_submit_order_call(self, order: FutureOrder) -> Calls:
        pass

    @abstractmethod
    async def get_close_order_call(self, order: BasicOrder) -> Calls:
        pass

    @abstractmethod
    async def get_total_position(self) -> PositionInfo:
        pass

