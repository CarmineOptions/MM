from abc import ABC, abstractmethod

from marketmaking.order import DesiredOrders
from state.state import State


class OrderChainElement(ABC):
    @abstractmethod
    def process(self, state: State, orders: DesiredOrders) -> DesiredOrders:
        pass
