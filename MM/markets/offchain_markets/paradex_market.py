
from decimal import Decimal
from typing import final

import httpx
from paradex_py.common.order import (
    Order as ParadexOrder, 
    OrderSide as ParadexOrderSide, 
    OrderType as ParadexOrderType
)

from marketmaking.order import AllOrders, BasicOrder, FutureOrder, OpenOrders, TerminalOrders
from markets.market import MarketConfig, OffchainMarketABC, PrologueOp_SeekLiquidity, PrologueOps
from state.account_state import PositionInfo
from state.state import State
from venues.paradex.paradex import ParadexClient, ParadexResponseOrder

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
        raise NotImplementedError("Market <> Market id still missing")
        
        _orders = await self._px.get_all_open_orders_for_market('BTC-USD-PERP')
        orders = [
            _paradex_order_to_basic_order(o, None) for o in _orders
        ]
        return AllOrders(
            active = OpenOrders.from_list(orders),
            terminal = TerminalOrders.from_list([])
        )


    def get_submit_order_call(self, order: FutureOrder) -> httpx.Request:
        raise NotImplementedError("Market <> Market id still missing")
        o = _future_order_to_paradex_order(order, None)
        return self._px.get_submit_single_order_request(o)
        

    def get_close_order_call(self, order: BasicOrder) -> httpx.Request:
        return self._px.get_cancel_order_request(id=str(order.order_id))

    async def get_total_position(self) -> PositionInfo:
        raise NotImplementedError

    def prologue_ops_to_calls(self, state: State, ops: list[PrologueOps]) -> list[httpx.Request]:

        calls: list[httpx.Request] = []
        for op in ops: 
            match op:
                case PrologueOp_SeekLiquidity(_):
                    continue

        return calls


def _paradex_order_to_basic_order(o: ParadexResponseOrder, market_id: int) -> BasicOrder:
    side = 'Bid' if o['side'] == 'BUY' else 'Ask'
    return BasicOrder(
        price = Decimal(o['price']),
        amount = Decimal(o['size']),
        amount_remaining= Decimal(o['remaining_size']),
        order_id = int(o['id']),
        market_id = market_id,
        order_side = side,
        entry_time = o['created_at'],
        venue = 'Paradex'
    )


def _future_order_to_paradex_order(o: FutureOrder, market: str) -> ParadexOrder:
    side = ParadexOrderSide.Buy if o.is_bid() else ParadexOrderSide.Buy
    return ParadexOrder(
        market = market,
        order_type = ParadexOrderType.Limit,
        order_side = side,
        size = o.amount,
        limit_price = o.price,
        instruction = 'POST_ONLY',
    )
