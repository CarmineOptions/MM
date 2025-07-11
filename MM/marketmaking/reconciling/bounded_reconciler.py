from decimal import Decimal
from typing import final

from state.state import State
from marketmaking.order import BasicOrder, DesiredOrders, OpenOrders
from marketmaking.reconciling.order_reconciler import OrderReconciler, ReconciledOrders


@final
class BoundedReconciler(OrderReconciler):
    '''
    A reconciler that limits the number of orders per side and ensures that
    orders are within a certain relative distance from the fair price.
    '''
    def __init__(
        self,
        max_relative_distance_from_fp: Decimal,
        min_relative_distnace_from_fp: Decimal,
        minimal_remaining_size: Decimal,  # in Base asset
        max_orders_per_side: int,
    ) -> None:
        self._max_relative_distance = max_relative_distance_from_fp
        self._min_relative_distance = min_relative_distnace_from_fp
        self._minimal_remaining_size = minimal_remaining_size
        self._max_orders_per_side = max_orders_per_side

        pass

    def reconcile(
        self, state: State, existing_orders: OpenOrders, desired_orders: DesiredOrders
    ) -> ReconciledOrders:
        # TODO: This reconciler is kinds weird now, because it doesn't
        # just reconcile the existing/desired, but it also applies some rules
        # to remove existing orders. For example if we add some element that
        # will shift orders based on position, then we'd also have to shift/remove
        # the existing ones based on those rules, which won't happen here.
        # It might also be that case that those shifted orders won't even be sent
        # to the market.
        # Generally, only reconciliation should happen here.

        reconciled = ReconciledOrders(to_cancel=[], to_place=[])

        bids_kept: list[BasicOrder] = []
        asks_kept: list[BasicOrder] = []
        for order in existing_orders.all_orders:
            if self._is_order_too_close(order, state):
                reconciled.to_cancel.append(order)
                continue

            if order.amount_remaining < self._minimal_remaining_size:
                reconciled.to_cancel.append(order)
                continue

            if order.is_bid():
                bids_kept.append(order)
            else:
                asks_kept.append(order)

        # Order lists from deepest orders to best ones
        bids_kept.sort(key=lambda x: -x.price)
        asks_kept.sort(key=lambda x: x.price)

        # Remove the deepest orders that are redundant
        reconciled.to_cancel += bids_kept[self._max_orders_per_side:]
        reconciled.to_cancel += asks_kept[self._max_orders_per_side:]

        bids_kept = bids_kept[:self._max_orders_per_side]
        asks_kept = asks_kept[:self._max_orders_per_side]

        if self._new_orders_needed(state, bids_kept):
            reconciled.to_place += desired_orders.bids

        if self._new_orders_needed(state, asks_kept):
            reconciled.to_place += desired_orders.asks

        return reconciled

    def _is_order_too_close(self, order: BasicOrder, state: State) -> bool:
        if order.is_bid():
            treshold = (1 - self._min_relative_distance) * state.fair_price
            return treshold < order.price

        treshold = (1 + self._min_relative_distance) * state.fair_price
        return treshold > order.price

    def _is_order_too_far(self, order: BasicOrder, state: State) -> bool:
        if order.is_bid():
            treshold = (1 - self._max_relative_distance) * state.fair_price
            return treshold > order.price

        treshold = (1 + self._max_relative_distance) * state.fair_price
        return treshold < order.price

    def _new_orders_needed(self, state: State, orders: list[BasicOrder]) -> bool:
        # New order is needed if there aren't any orders or they're too far
        if not orders:
            return True

        order = orders[0]
        return self._is_order_too_far(order, state)
