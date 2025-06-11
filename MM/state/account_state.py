

from marketmaking.order import OpenOrders
from marketmaking.waccount import WAccount
from marketmaking.market import Market



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
