
from decimal import Decimal
from typing import final
from marketmaking.order import DesiredOrders, FutureOrder
from state.state import State
from marketmaking.orderchain.order_chain import OrderChainElement

@final
class FixedParamsElement(OrderChainElement):
    """
    Constructs desired orders based on fixed params `target_relative_distance_from_FP`
    for the orders price and `order_size` for it's size.

    Ignores any input orders and returns new object so it's best to use as the head of the order chain.
    """
    def __init__(self, target_relative_distance_from_fp: Decimal, order_size_quote: Decimal):
        self._target_relative_distance = target_relative_distance_from_fp
        self._order_size = order_size_quote


    def process(self, state: State, orders: DesiredOrders) -> DesiredOrders:
        
        new_orders = DesiredOrders(
            bids = [],
            asks = []
        )
        
        optimal_bid_price = state.fair_price * (
            1 - self._target_relative_distance
        )
        optimal_bid_size = self._order_size / optimal_bid_price

        new_orders.bids.append(
            FutureOrder(
                order_side = 'bid',
                amount = optimal_bid_size,
                price = optimal_bid_price,
                platform = 'Starknet',
                venue = 'Remus'
            )
        )

        optimal_ask_price = state.fair_price * (
            1 + self._target_relative_distance
        )
        optimal_ask_size = self._order_size / optimal_ask_price

        new_orders.asks.append(
            FutureOrder(
                order_side = 'ask',
                amount = optimal_ask_size,
                price = optimal_ask_price,
                platform = 'Starknet',
                venue = 'Remus'
            )
        )

        return new_orders