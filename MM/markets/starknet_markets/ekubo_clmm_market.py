
import asyncio
from decimal import Decimal
import logging
from typing import final, TYPE_CHECKING

from starknet_py.net.client_models import Calls, Call
from starknet_py.contract import Contract

from state.state import State
from platforms.starknet.starknet_account import WAccount
from instruments.instrument import InstrumentAmount
from state.account_state import PositionInfo
from markets.market import PrologueOp_SeekLiquidity, PrologueOps
from marketmaking.order import AllOrders, BasicOrder, FutureOrder, OpenOrders
from markets.market import StarknetMarketABC
from venues.ekubo.ekubo import EkuboClient
from venues.ekubo.ekubo_market_configs import EkuboMarketConfig, get_preloaded_ekubo_clmm_market_config

if TYPE_CHECKING:
    from state.state import State

@final
class EkuboCLMMMarket(StarknetMarketABC):

    def __init__(
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


    @staticmethod
    async def new(account: WAccount, market_id: int) -> "EkuboCLMMMarket":
        client = await EkuboClient.from_account(account = account.account)
        market_config = get_preloaded_ekubo_clmm_market_config(market_id)
    
        if market_config is None:
            raise ValueError(f"No preloaded ekubo clmm config found for id `{market_id}`")
        
        base_token = await Contract.from_address(
            address = market_config.base_token.address,
            provider = account.account
        )
        quote_token = await Contract.from_address(
            address = market_config.quote_token.address,
            provider = account.account
        )
        return EkuboCLMMMarket(
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
        return await self._client.view.get_all_clmm_positions_as_limit_orders(
            wallet=self._account.address,
            market_cfg=self._market_config
        )

    def get_submit_order_call(self, order: FutureOrder) -> Calls:
        return self._client.prep_submit_position_call(
            order = order,
            market_cfg = self._market_config,
            base_token_contract= self._base_token,
            quote_token_contract = self._quote_token,
        )

    def get_close_order_call(self, order: BasicOrder) -> Calls:
        return self._client.prep_remove_position_call(
            order = order,
            cfg = self._market_config
        )

    def get_withdraw_call(self, state: "State", amount: InstrumentAmount) -> list[Call]:
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
            withdrawable_base=Decimal(0),
            withdrawable_quote=Decimal(0)
        )

    def seek_additional_liquidity(self, state: "State") -> Calls:
        return []

    def prologue_ops_to_calls(self, state: "State", ops: list[PrologueOps]) -> list[Calls]:
        calls = []

        for op in ops: 
            call = self._prologue_op_to_call(state, op)
            if call: 
                calls.append(call)

        return calls
    
    def _prologue_op_to_call(self, state: "State", op: PrologueOps) -> Calls | None:
        match op:
            case PrologueOp_SeekLiquidity(_):
                return None
    

def _get_base_quote_from_orders(orders: OpenOrders) -> tuple[Decimal, Decimal]:
    # There are some amounts in fees too which will distort the position,
    # but for this mvp it's fine
    
    quote_amt = Decimal(0)
    for bid in orders.bids:
        quote_amt += bid.amount_remaining * bid.price
        pass

    base_amt = Decimal(0)
    for ask in orders.asks:
        base_amt += ask.amount_remaining
        pass

    return base_amt, quote_amt
