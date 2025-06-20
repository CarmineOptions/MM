from abc import ABC, abstractmethod
from dataclasses import dataclass

from marketmaking.order import BasicOrder, DesiredOrders, FutureOrder, OpenOrders
from state.state import State


@dataclass
class ReconciledOrders:
    '''
    Represents the result of reconciling desired orders with existing open orders.
    '''
    to_cancel: list[BasicOrder]
    to_place: list[FutureOrder]


class OrderReconciler(ABC):
    '''
    Abstract base class for reconciling desired orders with existing open orders.
    This class defines the interface for reconciling orders.
    '''
    @abstractmethod
    def reconcile(
        self, state: State, existing_orders: OpenOrders, desired_orders: DesiredOrders
    ) -> ReconciledOrders:
        pass
