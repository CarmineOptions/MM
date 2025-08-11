import logging
from decimal import Decimal
from typing import final

from state.state import State
from marketmaking.order import BasicOrder, DesiredOrders, FutureOrder, OpenOrders
from marketmaking.reconciling.order_reconciler import OrderReconciler, ReconciledOrders


@final
class ToleranceOrderReconciler(OrderReconciler):
    '''
    Takes in price and quantity tolerance and for every desired orders it goes through the 
    list of already existing ones. If there is one that is within the tolerance bounds,
    it won't place that one and will keep the existing one instead.

    Compares asks with asks and bids with bids only.
    '''
    def __init__(self, relative_price_tolerance: Decimal, relative_quantity_tolerance: Decimal):
        self._logger = logging.getLogger(self.__class__.__name__)

        if relative_price_tolerance < 0: 
            raise ValueError(f"Invalid price tolerance {relative_price_tolerance=}")
        
        if relative_quantity_tolerance < 0:
            raise ValueError(f"Invalid quantity tolerance {relative_quantity_tolerance=}")
        
        self.relative_price_tolerance = relative_price_tolerance
        self.relative_quantity_tolerance = relative_quantity_tolerance

    def reconcile(self, state: State, existing_orders: OpenOrders, desired_orders: DesiredOrders) -> ReconciledOrders:
        remaining_existing_orders = list(existing_orders.all_orders) # to make a (shallow) copy
        
        to_place = []

        to_keep = []
        to_ignore = []
        
        for desired in desired_orders.all_orders:
            acceptable = self._get_acceptable_order(desired, remaining_existing_orders)
            if acceptable is None:
                to_place.append(desired)
            else:
                to_keep.append(acceptable)
                to_ignore.append(desired)
                remaining_existing_orders.remove(acceptable)

        # By this point we have removed all acceptable existing orders, so those that remain
        # should be cancelled.
        to_cancel = remaining_existing_orders

        self._logger.info(f"Ignoring desired orders: {to_ignore}")
        self._logger.info(f"Keeping resting orders: {to_keep}")
        self._logger.info(f"Canceling orders: {to_cancel}")
        self._logger.info(f"Placing orders: {to_place}")

        return ReconciledOrders(
            to_place=to_place,
            to_cancel=to_cancel
        )


    def _get_acceptable_order(self, desired_order: FutureOrder, current_orders: list[BasicOrder]) -> BasicOrder | None:
        for existing in current_orders:
            # FIXME: Will take first acceptable order, but there might be a better one down the line
            if self.is_within_tolerance( existing=existing, desired=desired_order):
                return existing
        return None


    def is_within_tolerance(self, existing: BasicOrder, desired: FutureOrder) -> bool:
        if existing.order_side != desired.order_side:
            return False

        # Check price tolerance
        price_tolerance  = existing.price * self.relative_price_tolerance
        if desired.price > (existing.price + price_tolerance):
            return False

        if desired.price < (existing.price - price_tolerance):
            return False

        # Check amt tolerance 
        quantity_tolerance = existing.amount * self.relative_quantity_tolerance
        if desired.amount < (existing.amount - quantity_tolerance):
            return False

        if desired.amount > (existing.amount + quantity_tolerance):
            return False

        return True