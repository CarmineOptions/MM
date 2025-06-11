
from marketmaking.orderchain.elements import get_element_from_name
from marketmaking.orderchain.elements.element import OrderChainElement
from cfg.cfg_classes import OrderChainElementConfig
from marketmaking.order import DesiredOrders
from state.state import State


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
    
    @staticmethod
    def from_config(chain: list[OrderChainElementConfig]) -> "OrderChain":
        elements = []

        for e in chain:
            elements.append(
                get_element_from_name(e.name, **e.args)
            )

        return OrderChain(
            elements = elements
        )
            