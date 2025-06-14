

import asyncio
from decimal import Decimal
from marketmaking.waccount import WAccount
from oracles.data_sources.data_source import DataSource
from state.account_state import AccountState
from marketmaking.market import Market

class State:
    def __init__(self, market: Market, account: WAccount, fair_price_fetcher: DataSource) -> None:
        self.account = AccountState(
            market = market,
            account = account
        )

        self._fp_fetcher = fair_price_fetcher
        self._fair_price = Decimal('0')

    async def update(self) -> None:
        _, fair_price = await asyncio.gather(
            self.account.update(),
            self._fp_fetcher.get_price()
        )

        self._fair_price = fair_price

    @property
    def fair_price(self) -> Decimal:
        return self._fair_price


