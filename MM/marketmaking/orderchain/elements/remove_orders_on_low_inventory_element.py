import logging
from typing import final
from marketmaking.orderchain.elements.element import OrderChainElement
from marketmaking.order import DesiredOrders
from state.state import State

# Note: In future maybe support just decreasing sizes of orders  or
# adding some buffer (eg. instead of checking full portfolio size do 
# sth like portfolio * 0.95)

@final
class RemoveOrdersOnLowInventoryElement(OrderChainElement):
    '''
    Element that checks current balances and available inventory and if there isn't enough
    balance to send an order, it removes it.
    '''
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def process(self, state: State, orders: DesiredOrders) -> DesiredOrders:
        new_desired = DesiredOrders(
            bids = [],
            asks = []
        )

        # Sort orders from best to worst, because we'll be seeking liquidity
        # and we want to process best orders first, so that if there is enough
        # only for some order to be kept, then better orders have higher chance of
        # being left in the book
        orders.asks.sort(key = lambda x: x.price)
        orders.bids.sort(key = lambda x: x.price, reverse= True)

        portfolio = state.account.position
        removed_orders = []

        total_quote_needed = 0
        for bid_order in orders.bids:
            order_quote_amount = bid_order.price * bid_order.amount
            if total_quote_needed + order_quote_amount <= portfolio.total_quote:
                new_desired.bids.append(bid_order)
                total_quote_needed += order_quote_amount
            else: 
                removed_orders.append(bid_order)
        
        total_base_needed = 0
        for ask_order in orders.asks:
            order_base_amount = ask_order.amount
            if total_base_needed + order_base_amount <= portfolio.total_base:
                new_desired.asks.append(ask_order)    
                total_base_needed += order_base_amount
            else:
                removed_orders.append(ask_order)

        # FIXME: Due to how current reconciler works, this could still fail if the reconciler
        # decides not to remove orders that we need to be removed in order to have enough 
        # liquidity. For now it's fine and new reconciler will be written soon

        self._logger.info(f"Removing future orders due to low inventory: {removed_orders}")

        return new_desired

