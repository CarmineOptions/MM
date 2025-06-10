from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import final

from state.account_state import OpenOrders
from marketmaking.order import BasicOrder, DesiredOrders, FutureOrder

@dataclass
class ReconciledOrders:
    to_cancel: list[BasicOrder]
    to_place: list[FutureOrder]

class OrderReconciler(ABC):
    @abstractmethod
    def reconcile(self, existing_orders: OpenOrders, desired_orders: DesiredOrders) -> ReconciledOrders:
        pass

@final
class AlwaysReplaceOrderReconciler(OrderReconciler):
    def __init__(self) -> None:
        pass

    def reconcile(self, existing_orders: OpenOrders, desired_orders: DesiredOrders) -> ReconciledOrders:
        return ReconciledOrders(
            to_cancel = existing_orders.all_orders,
            to_place = desired_orders.all_orders
        )

