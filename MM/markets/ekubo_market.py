import asyncio
from decimal import Decimal
import logging
from typing import final

from starknet_py.net.client_models import Calls
from starknet_py.contract import Contract

from instruments.instrument import InstrumentAmount
from marketmaking.market import PositionInfo
from marketmaking.order import AllOrders, BasicOrder, FutureOrder, OpenOrders, TerminalOrders
from marketmaking.waccount import WAccount
from markets.market import Market
from venues.ekubo.ekubo import EkuboClient
from venues.ekubo.ekubo_market_configs import EkuboMarketConfig, get_preloaded_ekubo_market_config

@final
class EkuboMarket(Market):

    def __init__(
        self,
        market_id: int, 
        market_config: EkuboMarketConfig,
        ekubo_client: EkuboClient,
        base_token: Contract,
        quote_token: Contract,
        account: WAccount
    ) -> None:
        self._market_id = market_id
        self._market_config = market_config
        self._client = ekubo_client
        self._base_token = base_token
        self._quote_token = quote_token
        self._account = account

        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)


    @staticmethod
    async def new(account: WAccount, market_id: int) -> "EkuboMarket":
        client = await EkuboClient.from_account(account = account.account)
        market_config = get_preloaded_ekubo_market_config(market_id)
    
        if market_config is None:
            raise ValueError(f"No preloaded ekubo config found for id `{market_id}`")
        
        base_token = await Contract.from_address(
            address = market_config.token0.address,
            provider = account.account
        )
        quote_token = await Contract.from_address(
            address = market_config.token1.address,
            provider = account.account
        )
        return EkuboMarket(
            market_id = market_id,
            market_config=market_config,
            ekubo_client=client,
            base_token=base_token,
            quote_token=quote_token,
            account=account
        )

    async def setup(self, wrapped_account: WAccount) -> None:
        pass

    async def get_current_orders(self) -> AllOrders:
        return await self._client.view.get_all_orders(
            wallet = self._account.address,
            market_cfg = self._market_config
        )

    async def get_submit_order_call(self, order: FutureOrder) -> Calls:
        return self._client.prep_submit_maker_order_call(
            order=order,
            market_cfg=self._market_config,
            base_token_contract=self._base_token,
            quote_token_contract=self._quote_token
        )
        
    async def get_close_order_call(self, order: BasicOrder) -> Calls:
        return self._client.prep_delete_maker_order_call(
            order = order,
            cfg = self._market_config
        )

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

        base_withdrawable, quote_withdrawable = _get_base_quote_withdrawable_from_terminal_orders(orders.terminal)

        base_in_orders, quote_in_orders = _get_base_quote_position_from_active_orders(orders.active)

        balance_base = Decimal(_balance_base[0]) / 10**self._market_config.token0.decimals
        balance_quote = Decimal(_balance_quote[0]) / 10**self._market_config.token1.decimals

        return PositionInfo(
            balance_base = balance_base,
            balance_quote=balance_quote,
            in_orders_base=base_in_orders,
            in_orders_quote=quote_in_orders,
            withdrawable_base=InstrumentAmount(
                instrument = self._market_config.token0,
                amount_raw = base_withdrawable * 10**self._market_config.token0.decimals
            ),
            withdrawable_quote=InstrumentAmount(
                instrument = self._market_config.token1,
                amount_raw = quote_withdrawable * 10**self._market_config.token1.decimals
            ),
        )

def _get_base_quote_withdrawable_from_terminal_orders(
    orders: TerminalOrders
) -> tuple[Decimal, Decimal]:

    base = Decimal(0)   
    for o in orders.bids:
        # bids buy the base token 
        # so if they are executed
        # then position is in base
        # same as the amount in orders
        base += o.amount

    quote = Decimal(0)
    for o in orders.asks:
        # asks sell base for quote
        # so calculate quote that 
        # is resting in the order
        quote += o.amount_remaining * o.price

    return base, quote

def _get_base_quote_position_from_active_orders(
    orders: OpenOrders
) -> tuple[Decimal, Decimal]:
    base = Decimal(0)   
    quote = Decimal(0)

    # Orders might have sth matched
    # but we can't withdraw just a part of it
    # so just calculate how much matched we have
    # and add it to the corresponding var for now
    for o in orders.bids:
        matched = o.amount - o.amount_remaining
        base += matched

        quote += o.amount_remaining * o.price

    for o in orders.asks:
        matched = o.amount - o.amount_remaining
        quote += matched * o.price
        base += o.amount_remaining

    return base, quote

    
