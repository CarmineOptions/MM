from typing import final

from marketmaking.order import DesiredOrders, OpenOrders
from marketmaking.reconciling.order_reconciler import OrderReconciler, ReconciledOrders
from state.state import State


@final
class AlwaysReplaceOrderReconciler(OrderReconciler):
    '''
    A reconciler that always replaces existing orders with desired orders.
    '''
    def __init__(self) -> None:
        pass

    def reconcile(
        self, _: State, existing_orders: OpenOrders, desired_orders: DesiredOrders
    ) -> ReconciledOrders:
        return ReconciledOrders(
            to_cancel=existing_orders.all_orders, to_place=desired_orders.all_orders
        )
