from dataclasses import dataclass


from marketmaking.order import BasicOrder
from marketmaking.waccount import WAccount
from marketmaking.market import Market

@dataclass
class OpenOrders:
    """
    Class that holds lists of bids and asks.
    """
    bids: list[BasicOrder]
    asks: list[BasicOrder]

    @staticmethod
    def from_list(orders: list[BasicOrder]) -> "OpenOrders":
        """
        Constructs list OpenOrders from list of BasicOrder, separating
        them into bids and asks. 
        
        Doesn't check if they are all from the same market/venue...
        """

        bids = []
        asks = []

        for o in orders:
            if o.order_side.lower() == 'bid':
                bids.append(o)
                continue

            asks.append(o)

        bids = sorted(bids, key=lambda x: -x.price)
        asks = sorted(asks, key=lambda x: -x.price)

        return OpenOrders(
            bids = bids,
            asks = asks
        )


class AccountState:
    '''
    Class that holds info about current state of the trading account - orders, ivnentory etc.
    '''
    def __init__(self, market: Market, account: WAccount) -> None:
        self.market = market
        self.account = account

        self._open_orders: OpenOrders = OpenOrders(
            bids = [],
            asks = []
        )
        
    @property
    def open_orders(self) -> OpenOrders:
        return self._open_orders
    
    async def update(self) -> None:

        orders = await self.market.remus_client.view.get_all_user_orders_for_market_id(
            address=self.account.address, market_id=self.market.market_id
        )

        self._open_orders = OpenOrders.from_list(orders)
