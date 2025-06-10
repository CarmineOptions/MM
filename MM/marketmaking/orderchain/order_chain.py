from abc import ABC, abstractmethod

from marketmaking.order import DesiredOrders, FutureOrder
from state.state import State

class OrderChainElement(ABC):

    @abstractmethod
    def process(self, state: State, orders: DesiredOrders) -> DesiredOrders:
        pass

class OrderChain:
    def __init__(self, elements: list[OrderChainElement]) -> None:
        self.elements = elements

    def process(self, state: State) -> DesiredOrders:
        orders: DesiredOrders = DesiredOrders(
            bids = [],
            asks = []
        )

        for element in self.elements:
            orders = element.process(state = state, orders = orders)

        return orders
