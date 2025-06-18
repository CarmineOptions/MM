import asyncio
from marketmaking.order import AllOrders, OpenOrders, TerminalOrders
from marketmaking.waccount import WAccount
from markets.market import PositionInfo, Market


class AccountState:
    """
    Class that holds info about current state of the trading account - orders, ivnentory etc.
    """

    def __init__(self, market: Market, account: WAccount) -> None:
        self.market = market
        self.account = account

        self._position = PositionInfo.empty(
            base_token=market.market_cfg.base_token,
            quote_token=market.market_cfg.quote_token
        )
        self._orders: AllOrders = AllOrders(
            active = OpenOrders(
                bids = [],
                asks = []
            ),
            terminal = TerminalOrders(
                bids = [],
                asks = []
            )
        )

    @property
    def orders(self) -> AllOrders:
        return self._orders

    @property
    def position(self) -> PositionInfo:
        return self._position

    async def update(self) -> None:
        async with asyncio.TaskGroup() as tg:
            # TODO: We're fetching position here which fetches orders for market,
            #  but then we're doing it again below, we could just use the same orders
            position_task = tg.create_task(
                self.market.get_total_position()
            )
            orders_task = tg.create_task(
                self.market.get_current_orders()
            )

        position = position_task.result()
        orders = orders_task.result()

        self._position = position
        self._orders = orders
