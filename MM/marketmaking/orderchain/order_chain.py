from marketmaking.orderchain.elements import get_element_from_name
from marketmaking.orderchain.elements.element import OrderChainElement
from cfg.cfg_classes import OrderChainElementConfig
from marketmaking.order import DesiredOrders
from state.state import State


class OrderChain:
    '''
    Represents a chain of order processing elements that can be applied sequentially
    to generate desired orders based on the current state.
    Each element in the chain processes the state and modifies the desired orders
    according to its specific logic.
    '''
    def __init__(self, elements: list[OrderChainElement]) -> None:
        self.elements = elements

    def process(self, state: State) -> DesiredOrders:
        '''
        Processes the given state through all elements in the order chain,
        generating a final set of desired orders.
        '''
        orders: DesiredOrders = DesiredOrders(bids=[], asks=[])

        for element in self.elements:
            orders = element.process(state=state, orders=orders)

        return orders

    @staticmethod
    def from_config(chain: list[OrderChainElementConfig]) -> "OrderChain":
        elements = []

        for e in chain:
            elements.append(get_element_from_name(e.name, **e.args))

        return OrderChain(elements=elements)
