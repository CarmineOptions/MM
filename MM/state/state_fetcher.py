import asyncio
from decimal import Decimal

from starknet_py.net.client_models import Calls
import httpx

from .state import State
from oracles.data_sources.data_source import DataSource
from state.account_state import AccountState
from markets.market import MarketABC


class PollingStateFetcher:

    def __init__(self, market: MarketABC[Calls | httpx.Request], fair_price_fetcher: DataSource):
        self._market = market
        self._fp_fetcher = fair_price_fetcher

    async def get_state(self) -> State:
        async with asyncio.TaskGroup() as tg:
            acc_task = tg.create_task(
                self._get_account_state()
            )
            fp_task = tg.create_task(
                self._get_fair_price()
            )

        acc_state = acc_task.result()
        fair_price = fp_task.result()

        return State(
            account = acc_state,
            _fair_price = fair_price
        )


    async def _get_account_state(self) -> AccountState:

        async with asyncio.TaskGroup() as tg:
            position_task = tg.create_task(
                self._market.get_total_position()
            )
            orders_task = tg.create_task(
                self._market.get_current_orders()
            )
        
        position = position_task.result()
        orders = orders_task.result()

        return AccountState(
            position=position,
            orders = orders
        )
    
    async def _get_fair_price(self) -> Decimal:
        return await self._fp_fetcher.get_price()

