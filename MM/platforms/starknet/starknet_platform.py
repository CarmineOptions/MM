from typing import final, TYPE_CHECKING
import logging

from starknet_py.net.client_errors import ClientError
from markets.market import StarknetMarketABC, PrologueOps
from platforms.starknet.starknet_account import WAccount, get_wrapped_account
from cfg.cfg_classes import StrategyConfig
from marketmaking.reconciling.order_reconciler import ReconciledOrders
from markets import get_starknet_market
from tx_builders.tx_builder import TxBuilder
from tx_builders import get_tx_builder

from ..platform_abc import PlatformABC

if TYPE_CHECKING:
    from state.state import State


@final
class StarknetPlatform(PlatformABC):

    def __init__(self, w_account: WAccount, market: StarknetMarketABC, tx_builder: TxBuilder): 
        self._waccount = w_account
        self._market = market
        self._tx_builder = tx_builder

    @staticmethod
    async def from_config(cfg: StrategyConfig) -> "StarknetPlatform":
        platform_cfg = cfg.platform.config
        market_cfg = cfg.market
        w_account = get_wrapped_account(platform_cfg.account)

        market = await get_starknet_market(market_cfg.venue, account = w_account, market_id = market_cfg.market_id)
        tx_builder = get_tx_builder(platform_cfg.tx_builder.name, market)

        return StarknetPlatform(
            w_account=w_account,
            market = market,
            tx_builder=tx_builder
        )

    async def initialize_trading(self) -> None:
        await self._market.setup()


    async def execute_operations(self, state: "State", prologue: list[PrologueOps], ops: ReconciledOrders) -> None:
        
        prologue_calls = self.market.prologue_ops_to_calls(state, prologue)

        await self._tx_builder.build_and_execute_transactions(
            wrapped_account=self._waccount,
            reconciled_orders=ops,
            prologue = prologue_calls
        )

    async def reset(self) -> None:
        await self._waccount.reset_latest_nonce()


    async def error_handled(self, e: Exception) -> bool:

        if isinstance(e, ClientError) and "Account nonce" in e.message:
            logging.error("Account nonce error encountered. Reinitializing account")

            await self.reset()

            return True
        
        return False


    @property
    def market(self) -> StarknetMarketABC:
        return self._market