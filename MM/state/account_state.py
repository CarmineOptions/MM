import asyncio
from marketmaking.order import OpenOrders
from marketmaking.waccount import WAccount
from marketmaking.market import Market, PositionInfo


class AccountState:
    """
    Class that holds info about current state of the trading account - orders, ivnentory etc.
    """

    def __init__(self, market: Market, account: WAccount) -> None:
        self.market = market
        self.account = account

        self._position = PositionInfo.empty()
        self._open_orders: OpenOrders = OpenOrders(bids=[], asks=[])

    @property
    def open_orders(self) -> OpenOrders:
        return self._open_orders

    @property
    def position(self) -> PositionInfo:
        return self._position

    async def update(self) -> None:
        async with asyncio.TaskGroup() as tg:
            position_task = tg.create_task(
                self.market.get_total_position(self.account.address)
            )
            orders_task = tg.create_task(
                self.market.remus_client.view.get_all_user_orders_for_market_id(
                    address=self.account.address, market_id=self.market.market_id
                )
            )

        position = position_task.result()
        orders = orders_task.result()

        self._position = position
        self._open_orders = OpenOrders.from_list(orders)
