import asyncio
from decimal import Decimal
import logging
from typing import final

from starknet_py.contract import Contract
from starknet_py.net.client_models import Calls

from markets.market import PositionInfo
from marketmaking.waccount import WAccount
from venues.remus.remus import RemusDexClient
from marketmaking.order import AllOrders, BasicOrder, FutureOrder
from .market import Market
from venues.remus.remus_market_configs import RemusMarketConfig, get_preloaded_remus_market_config

MAX_UINT = 2**256 - 1

@final
class RemusMarket(Market):

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

    async def setup(self, account: WAccount) -> None:

        nonce = await account.get_nonce()

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
            hex(account.address),
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
            hex(account.address),
            hex(self._market_config.quote_token.address),
        )
        self._logger.info("Set unlimited approval for address")

        await account.set_latest_nonce(nonce)
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
            self._base_token.functions["balanceOf"].call(account=self._account.account),
            self._quote_token.functions["balanceOf"].call(account=self._account.account),
        )

        # Remus has no terminal orders so we only account the active ones
        orders_base, orders_quote = _get_base_quote_position_from_active_orders(orders.active.all_orders)

        return PositionInfo(
            balance_base=Decimal(balance_base[0])
                / 10**self._market_config.base_token.decimals,
            balance_quote=Decimal(balance_quote[0])
                / 10**self._market_config.quote_token.decimals,
            withdrawable_base=claimable_base,
            withdrawable_quote=claimable_quote,
            in_orders_base=orders_base,
            in_orders_quote=orders_quote,
        )


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