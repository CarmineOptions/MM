
from typing import final

import httpx

from instruments.instrument import InstrumentAmount
from marketmaking.order import AllOrders, BasicOrder, FutureOrder
from markets.market import MarketConfig, OffchainMarketABC, PositionInfo, PrologueOps
from state.state import State
from venues.paradex.paradex import ParadexClient

@final
class ParadexMarket(OffchainMarketABC):

    def __init__(self, l1_address: str, l2_private_key: str):
        self._px = ParadexClient(
            l1_address=l1_address,
            l2_private_key=l2_private_key
        )

    @property
    def market_cfg(self) -> MarketConfig:
        raise NotImplementedError

    async def setup(self) -> None:
        pass

    async def get_current_orders(self) -> AllOrders:
        raise NotImplementedError

    def get_submit_order_call(self, order: FutureOrder) -> httpx.Request:
        raise NotImplementedError

    def get_close_order_call(self, order: BasicOrder) -> httpx.Request:
        return self._px.get_cancel_order_request(id=str(order.order_id))

    def get_withdraw_call(self, state: State, amount: InstrumentAmount) -> httpx.Request:
        raise NotImplementedError

    async def get_total_position(self) -> PositionInfo:
        raise NotImplementedError

    def seek_additional_liquidity(self, state: State) -> httpx.Request:
        raise NotImplementedError

    def prologue_ops_to_calls(self, state: State, ops: list[PrologueOps]) -> list[httpx.Request]:
        raise NotImplementedError
