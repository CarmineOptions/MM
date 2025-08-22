import asyncio
from decimal import Decimal
import logging
from typing import final, TYPE_CHECKING

from starknet_py.net.client_models import Calls, Call
from starknet_py.contract import Contract

from platforms.starknet.starknet_account import WAccount
from instruments.instrument import InstrumentAmount
from state.account_state import PositionInfo
from markets.market import PrologueOp_SeekLiquidity, PrologueOps
from marketmaking.order import AllOrders, BasicOrder, FutureOrder, OpenOrders, TerminalOrders
from markets.market import StarknetMarketABC
from venues.ekubo.ekubo import EkuboClient
from venues.ekubo.ekubo_market_configs import EkuboMarketConfig, get_preloaded_ekubo_limit_order_market_config

if TYPE_CHECKING:
    from state.state import State
@final
class EkuboLimitOrderMarket(StarknetMarketABC):

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
    async def new(account: WAccount, market_id: int) -> "EkuboLimitOrderMarket":
        client = await EkuboClient.from_account(account = account.account)
        market_config = get_preloaded_ekubo_limit_order_market_config(market_id)
    
        if market_config is None:
            raise ValueError(f"No preloaded ekubo config found for id `{market_id}`")
        
        base_token = await Contract.from_address(
            address = market_config.base_token.address,
            provider = account.account
        )
        quote_token = await Contract.from_address(
            address = market_config.quote_token.address,
            provider = account.account
        )
        return EkuboLimitOrderMarket(
            market_id = market_id,
            market_config=market_config,
            ekubo_client=client,
            base_token=base_token,
            quote_token=quote_token,
            account=account
        )

    @property
    def market_cfg(self) -> EkuboMarketConfig:
        return self._market_config

    async def setup(self) -> None:
        pass

    async def get_current_orders(self) -> AllOrders:
        return await self._client.view.get_all_limit_orders(
            wallet = self._account.address,
            market_cfg = self._market_config
        )

    def get_submit_order_call(self, order: FutureOrder) -> Calls:
        return self._client.prep_submit_maker_order_call(
            order=order,
            market_cfg=self._market_config,
            base_token_contract=self._base_token,
            quote_token_contract=self._quote_token
        )
        
    def get_close_order_call(self, order: BasicOrder) -> Calls:
        return self._client.prep_delete_maker_order_call(
            order = order,
            cfg = self._market_config
        )
    
    def seek_additional_liquidity(self, state: "State") -> Calls:
        # No locked liquidity in ekubo
        return []

    def get_withdraw_call(self, state: "State", bids: bool) -> list[Call]:
        # Withdrawing in ekubo is basically closing executed orders
        if bids:
            # We want to withdraw base token, so we need to close 
            # matched bid orders since those are the ones 
            # where we sold quote in exchange for base 
            # so base is pending there
            to_close = state.account.orders.terminal.bids
        else: 
            # vice versa
            to_close = state.account.orders.terminal.asks

        calls = [
            self._client.prep_delete_maker_order_call(
                order = o,
                cfg = self._market_config
            )
            for o in to_close
        ]
        return calls

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

        balance_base = Decimal(_balance_base[0]) / 10**self._market_config.base_token.decimals
        balance_quote = Decimal(_balance_quote[0]) / 10**self._market_config.quote_token.decimals

        return PositionInfo(
            balance_base = balance_base,
            balance_quote=balance_quote,
            in_orders_base=base_in_orders,
            in_orders_quote=quote_in_orders,
            withdrawable_base=base_withdrawable,
            withdrawable_quote=quote_withdrawable
        )

    def prologue_ops_to_calls(self, state: "State", ops: list[PrologueOps]) -> list[Calls]:
        calls = []

        for op in ops: 
            call = self._prologue_op_to_call(state, op)
            calls.append(call)

        return calls
    
    def _prologue_op_to_call(self, state: "State", op: PrologueOps) -> Calls:
        match op:
            case PrologueOp_SeekLiquidity(_):
                bids = self.get_withdraw_call(state, True)
                asks = self.get_withdraw_call(state, False)
                return bids + asks


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

    
