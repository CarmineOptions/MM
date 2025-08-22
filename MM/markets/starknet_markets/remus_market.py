import asyncio
from decimal import Decimal
import logging
from typing import Iterable, final, TYPE_CHECKING

from starknet_py.contract import Contract
from starknet_py.net.client_models import Calls, Call

from markets.market import PrologueOps, PrologueOp_SeekLiquidity
from platforms.starknet.starknet_account import WAccount
from state.account_state import PositionInfo
from venues.remus.remus import RemusDexClient
from marketmaking.order import AllOrders, BasicOrder, FutureOrder
from markets.market import StarknetMarketABC
from venues.remus.remus_market_configs import RemusMarketConfig, get_preloaded_remus_market_config

if TYPE_CHECKING:
    from state.state import State

MAX_UINT = 2**256 - 1

@final
class RemusMarket(StarknetMarketABC):

    def __init__(
        self, 
        market_id: int, 
        market_config: RemusMarketConfig,
        remus_client: RemusDexClient,
        base_token_contract: Contract,
        quote_token_contract: Contract,
        account: WAccount
    ) -> None:
        self._market_id = market_id
        self._market_config = market_config
        self._client = remus_client
        self._base_token = base_token_contract
        self._quote_token = quote_token_contract
        self._account = account

        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    async def new(account: WAccount, market_id: int) -> "RemusMarket":
        client = await RemusDexClient.from_account(account = account.account)
        market_config = get_preloaded_remus_market_config(market_id)
    
        if market_config is None:
            raise ValueError(f"No preloaded remus config found for id `{market_id}`")
        
        base_token = await Contract.from_address(
            address = market_config.base_token.address,
            provider = account.account
        )
        quote_token = await Contract.from_address(
            address = market_config.quote_token.address,
            provider = account.account
        )

        return RemusMarket(
            market_id = market_id,
            market_config=market_config,
            remus_client=client,
            base_token_contract=base_token,
            quote_token_contract=quote_token,
            account=account
        )

    @property
    def market_cfg(self) -> RemusMarketConfig:
        return self._market_config

    async def get_current_orders(self) -> AllOrders:
        return await self._client.view.get_all_user_orders_for_market_id(
            address=self._account.address, market_id=self._market_id
        )

    def get_submit_order_call(self, order: FutureOrder) -> Calls:
        return self._client.prep_submit_maker_order_call(
            order = order,
            market_cfg = self._market_config
        )

    def get_close_order_call(self, order: BasicOrder) -> Calls:
        return self._client.prep_delete_maker_order_call(
            order = order
        )
    
    def get_withdraw_call(self, state: "State", amount: Decimal, is_base: bool) -> Calls:
        if is_base:
            token = self.market_cfg.base_token
            amount_raw = int(amount * 10**token.decimals)
        else:
            token = self.market_cfg.quote_token
            amount_raw = int(amount * 10**token.decimals)
        return self._client.prep_claim_call(amount=amount_raw, token_address=hex(token.address))
    

    def seek_additional_liquidity(self, state: "State") -> Calls:

        logging.info("Claiming tokens for market_id: %s", self.market_cfg.market_id)

        calls: list[Call] = []

        # Claim base token
        base_amt = state.account.position.withdrawable_base
        if base_amt:
            self._logger.info(
                "Claimable base amount is %s for token %s, preparing claim call",
                base_amt,
                hex(self.market_cfg.base_token.address),
            )
            call = self.get_withdraw_call(state = state, amount = base_amt, is_base=True)
            if isinstance(call, Iterable):
                calls += list(call)
            else:
                calls.append(call)
        else: 
            self._logger.info("No claimable for base token %s", hex(self.market_cfg.base_token.address))
        
        # Claim quote token
        quote_amt = state.account.position.withdrawable_quote
        if quote_amt:
            self._logger.info(
                "Claimable quote amount is %s for token %s, preparing claim call",
                quote_amt,
                hex(self.market_cfg.quote_token.address),
            )
            call = self.get_withdraw_call(state = state, amount = quote_amt, is_base=True)

            if isinstance(call, Iterable):
                calls += list(call)
            else:
                calls.append(call)
        else: 
            self._logger.info("No claimable for quote token %s", hex(self.market_cfg.base_token.address))
        
        return calls
        

    async def setup(self) -> None:

        nonce = await self._account.get_nonce()

        # Approve base token
        await (
            await self._base_token.functions["approve"].invoke_v3(
                spender=int(self._client.address, 16),
                amount=MAX_UINT,
                nonce=nonce,
                auto_estimate=True,
            )
        ).wait_for_acceptance()
        nonce += 1
        self._logger.info(
            "Set unlimited approval for address: %s, base token: %s",
            hex(self._account.address),
            hex(self._market_config.base_token.address),
        )

        # Approve quote token
        await (
            await self._quote_token.functions["approve"].invoke_v3(
                spender=int(self._client.address, 16),
                amount=MAX_UINT,
                nonce=nonce,
                auto_estimate=True,
            )
        ).wait_for_acceptance()
        nonce += 1
        self._logger.info(
            "Set unlimited approval for address: %s, quote token: %s",
            hex(self._account.address),
            hex(self._market_config.quote_token.address),
        )

        await self._account.set_latest_nonce(nonce)
        self._logger.info("Setting unlimited approvals is done.")

    async def get_total_position(self) -> PositionInfo:

        (
            orders,
            claimable_base,
            claimable_quote,
            balance_base,
            balance_quote,
        ) = await asyncio.gather(
            self.get_current_orders(),
            self._client.view.get_claimable(
                self._market_config.base_token, self._account.address
            ),
            self._client.view.get_claimable(
                self._market_config.quote_token, self._account.address
            ),
            self._base_token.functions["balanceOf"].call(account=self._account.account.address),
            self._quote_token.functions["balanceOf"].call(account=self._account.account.address),
        )

        # Remus has no terminal orders so we only account the active ones
        orders_base, orders_quote = _get_base_quote_position_from_active_orders(orders.active.all_orders)

        claimable_base_hr = claimable_base / 10**self.market_cfg.base_token.decimals
        claimable_quote_hr = claimable_quote / 10**self.market_cfg.quote_token.decimals

        return PositionInfo(
            balance_base=Decimal(balance_base[0])
                / 10**self._market_config.base_token.decimals,
            balance_quote=Decimal(balance_quote[0])
                / 10**self._market_config.quote_token.decimals,
            withdrawable_base=claimable_base_hr,
            withdrawable_quote=claimable_quote_hr,
            in_orders_base=orders_base,
            in_orders_quote=orders_quote,
        )
    
    def prologue_ops_to_calls(self, state: "State", ops: list[PrologueOps]) -> list[Calls]:
        calls = []

        for op in ops: 
            calls.append(
                self._prologue_op_to_call(state, op)
            )

        return calls
    
    def _prologue_op_to_call(self, state: "State", op: PrologueOps) -> Calls:
        match op:
            case PrologueOp_SeekLiquidity(_):
                return self.seek_additional_liquidity(state)


def _get_base_quote_position_from_active_orders(
    orders: list[BasicOrder],
) -> tuple[Decimal, Decimal]:
    base = Decimal(0)
    quote = Decimal(0)

    for o in orders:
        if o.order_side.lower() == "ask":
            base += o.amount_remaining
            continue
        # bid order
        quote += o.amount_remaining * o.price

    return base, quote