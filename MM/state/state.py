from dataclasses import dataclass
from decimal import Decimal
import logging


from state.account_state import AccountState


@dataclass
class State:
    account: AccountState
    _fair_price: Decimal

    @property
    def fair_price(self) -> Decimal:
        return self._fair_price

    @fair_price.setter
    def fair_price(self, new_fp: Decimal) -> None:
        logging.info(f"Updating fair price from {self._fair_price} to {new_fp}")
        self._fair_price = new_fp


# class State:
#     '''
#     State class that holds the current state for the trading strategy.
#     It contains the account state and the fair price fetcher.
#     '''
#     def __init__(
#         self, market: MarketABC[Calls | Request], account: WAccount, fair_price_fetcher: DataSource
#     ) -> None:
#         self.account = AccountState(market=market, account=account)

#         self._fp_fetcher = fair_price_fetcher
#         self._fair_price = Decimal("0")

#     async def update(self) -> None:
#         _, fair_price = await asyncio.gather(
#             self.account.update(), self._fp_fetcher.get_price()
#         )

#         self._fair_price = fair_price

#     @property
#     def fair_price(self) -> Decimal:
#         return self._fair_price

#     @fair_price.setter
#     def fair_price(self, new_fp: Decimal) -> None:
#         logging.info(f"Updating fair price from {self._fair_price} to {new_fp}")
#         self._fair_price = new_fp
