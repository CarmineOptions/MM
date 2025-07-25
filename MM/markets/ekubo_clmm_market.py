
import asyncio
from decimal import Decimal
import logging
from typing import final, TYPE_CHECKING

from starknet_py.net.client_models import Calls, Call
from starknet_py.contract import Contract

from MM.markets.market import MarketConfig
from MM.state.state import State
from instruments.instrument import InstrumentAmount
from markets.market import PositionInfo
from marketmaking.order import AllOrders, BasicOrder, FutureOrder, OpenOrders, TerminalOrders
from marketmaking.waccount import WAccount
from markets.market import Market
from venues.ekubo.ekubo import EkuboClient
from venues.ekubo.ekubo_market_configs import EkuboMarketConfig

if TYPE_CHECKING:
    from state.state import State

@final
class EkuboCLMMMarket(Market):

    def init(
        self,
        market_id: int, 
        market_config: EkuboMarketConfig,
        ekubo_client: EkuboClient,
        base_token: Contract,
        quote_token: Contract,
        account: WAccount
    ):
        self._market_id = market_id
        self._market_config = market_config
        self._client = ekubo_client
        self._base_token = base_token
        self._quote_token = quote_token
        self._account = account

        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        pass

    @property
    def market_cfg(self) -> EkuboMarketConfig:
        return self._market_config

    async def setup(self, wrapped_account: WAccount) -> None:
        pass

    async def get_current_orders(self) -> AllOrders:
        return await self._client.view.get_all_clmm_positions_as_limit_orders(
            wallet=self._account.address,
            market_cfg=self._market_config
        )

    def get_submit_order_call(self, order: FutureOrder) -> list[Call]:
        raise NotImplementedError

    def get_close_order_call(self, order: BasicOrder) -> list[Call]:
        raise NotImplementedError

    def get_withdraw_call(self, state: State, amount: InstrumentAmount) -> list[Call]:
        # No withdraws here since positions are never "filled" - they stay in the market
        return []

    async def get_total_position(self) -> PositionInfo:
        (
            orders,
            _balance_base,
            _balance_quote
        ) = await asyncio.gather(
            self.get_current_orders(),
            self._base_token.functions['balanceOf'].call(
                account = self._account.address
            ),
            self._quote_token.functions['balanceOf'].call(
                account = self._account.address
            )
        )


        balance_base = Decimal(_balance_base[0]) / 10**self._market_config.base_token.decimals
        balance_quote = Decimal(_balance_quote[0]) / 10**self._market_config.quote_token.decimals

        base_in_orders, quote_in_orders = _get_base_quote_from_orders(orders.active)

        return PositionInfo(
            balance_base = balance_base,
            balance_quote=balance_quote,
            in_orders_base=base_in_orders,
            in_orders_quote=quote_in_orders,
            withdrawable_base=InstrumentAmount(
                instrument = self._market_config.base_token,
                amount_raw = 0 
            ),
            withdrawable_quote=InstrumentAmount(
                instrument = self._market_config.quote_token,
                amount_raw = 0 
            ),
        )


    

def _get_base_quote_from_orders(orders: OpenOrders) -> tuple[Decimal, Decimal]:
    # There are some amounts in fees too which will distort the position,
    # but for this mvp it's fine
    
    quote_amt = Decimal(0)
    for bid in orders.bids:
        quote_amt += bid.amount_remaining * bid.price
        pass

    base_amt = Decimal(0)
    for ask in orders.asks:
        base_amt += ask.amount_remaining * ask.price
        pass

    return base_amt, quote_amt
