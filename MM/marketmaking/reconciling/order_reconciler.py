from abc import ABC, abstractmethod
from dataclasses import dataclass

from marketmaking.order import BasicOrder, DesiredOrders, FutureOrder, OpenOrders
from state.state import State

@dataclass
class ReconciledOrders:
    to_cancel: list[BasicOrder]
    to_place: list[FutureOrder]

class OrderReconciler(ABC):
    @abstractmethod
    def reconcile(self, state: State, existing_orders: OpenOrders, desired_orders: DesiredOrders) -> ReconciledOrders:
        pass

