
from decimal import Decimal
from typing import final
from marketmaking.orderchain.elements.element import OrderChainElement
from marketmaking.order import BasicOrder, DesiredOrders, FutureOrder
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
        self._max_relative_distance = max_relative_distance_from_fp
        self._min_relative_distance = min_relative_distance_from_fp

    def process(self, state: State, orders: DesiredOrders) -> DesiredOrders:
        
        new_orders = DesiredOrders(
            bids = [],
            asks = []
        )

        for bid in orders.bids:
            min_threshold = (1 - self._min_relative_distance) * state.fair_price
            if min_threshold < bid.price:
                new_orders.bids.append(
                    FutureOrder(
                        order_side=bid.order_side,
                        amount = bid.amount,
                        price = min_threshold,
                        platform = bid.platform,
                        venue = bid.venue
                    )
                )
                continue

            max_threshold = (1 - self._max_relative_distance) * state.fair_price
            if max_threshold > bid.price:
                new_orders.bids.append(
                    FutureOrder(
                        order_side=bid.order_side,
                        amount = bid.amount,
                        price = max_threshold,
                        platform = bid.platform,
                        venue = bid.venue
                    )
                )
                continue
            
            new_orders.bids.append(bid)
            
        for ask in orders.asks:
            min_threshold = (1 + self._min_relative_distance) * state.fair_price
            if min_threshold > ask.price:
                new_orders.asks.append(
                    FutureOrder(
                        order_side=ask.order_side,
                        amount=ask.amount,
                        price=min_threshold,
                        platform=ask.platform,
                        venue=ask.venue
                    )
                )
                continue

            max_threshold = (1 + self._max_relative_distance) * state.fair_price
            if max_threshold < ask.price:
                new_orders.asks.append(
                    FutureOrder(
                        order_side=ask.order_side,
                        amount = ask.amount,
                        price = max_threshold,
                        platform = ask.platform,
                        venue = ask.venue
                    )
                )
                continue

            new_orders.asks.append(ask)


        return new_orders
    
