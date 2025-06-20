from abc import ABC, abstractmethod

from marketmaking.order import DesiredOrders
from state.state import State


class OrderChainElement(ABC):
    '''
    Abstract base class for elements in the order chain.
    Each element processes the current state and modifies the desired orders
    according to its specific logic.
    '''
    @abstractmethod
    def process(self, state: State, orders: DesiredOrders) -> DesiredOrders:
        pass
