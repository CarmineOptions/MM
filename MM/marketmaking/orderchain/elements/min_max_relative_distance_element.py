from dataclasses import replace

from decimal import Decimal
from typing import final
from marketmaking.orderchain.elements.element import OrderChainElement
from marketmaking.order import DesiredOrders
from state.state import State


@final
class MinMaxRelativeDistanceElement(OrderChainElement):
    """
    An order chain element that ensures that orders are within a certain relative distance
    from the fair price. It modifies the orders in the desired orders, meaning it won't delete
    orders that are too close or too far, but it will adjust their prices to be within the specified
    bounds.
    """
    def __init__(
            self,
            max_relative_distance_from_fp: Decimal,
            min_relative_distance_from_fp: Decimal,
    ) -> None:
        #  TODO: Add `strategy` param eg with values "clip", "remove" that dicstates
        self._max_relative_distance = max_relative_distance_from_fp
        self._min_relative_distance = min_relative_distance_from_fp

        if not (0 <= min_relative_distance_from_fp <= max_relative_distance_from_fp):
            raise ValueError(
                f"Invalid params: {min_relative_distance_from_fp=} {max_relative_distance_from_fp=}"
            )

    def process(self, state: State, orders: DesiredOrders) -> DesiredOrders:
        
        new_orders = DesiredOrders(
            bids = [],
            asks = []
        )

        min_bid_threshold = (1 - self._min_relative_distance) * state.fair_price
        max_bid_threshold = (1 - self._max_relative_distance) * state.fair_price
        for bid in orders.bids:
            if min_bid_threshold < bid.price:
                new_orders.bids.append(
                    replace(
                        bid,
                        price = min_bid_threshold
                    )
                )
                continue

            if max_bid_threshold > bid.price:
                new_orders.bids.append(
                    replace(
                        bid,
                        price = max_bid_threshold
                    )
                )
                continue
            
            new_orders.bids.append(bid)
            
        min_ask_threshold = (1 + self._min_relative_distance) * state.fair_price
        max_ask_threshold = (1 + self._max_relative_distance) * state.fair_price
        for ask in orders.asks:
            if min_ask_threshold > ask.price:
                new_orders.asks.append(
                    replace(
                        ask,
                        price = min_ask_threshold
                    )
                )
                continue

            if max_ask_threshold < ask.price:
                new_orders.asks.append(
                    replace(
                        ask,
                        price = max_ask_threshold
                    )
                )
                continue

            new_orders.asks.append(ask)

        return new_orders
    
