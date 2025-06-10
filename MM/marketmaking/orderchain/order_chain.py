from abc import ABC, abstractmethod

from marketmaking.order import FutureOrder
from state.state import State

class OrderChainElement(ABC):

    @abstractmethod
    def process(self, state: State, orders: list[FutureOrder]) -> list[FutureOrder]:
        pass

class OrderChain:
    def __init__(self, elements: list[OrderChainElement]) -> None:
        self.elements = elements

    def process(self, state: State) -> list[FutureOrder]:
        orders: list[FutureOrder] = []

        for element in self.elements:
            orders = element.process(state = state, orders = orders)

        return orders
