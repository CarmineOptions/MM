from typing import final

from platforms.starknet.starknet_account import WAccount, get_wrapped_account
from cfg.cfg_classes import StrategyConfig
from marketmaking.reconciling.order_reconciler import ReconciledOrders
from markets import get_market
from markets.market import Market
from tx_builders.tx_builder import TxBuilder
from tx_builders import get_tx_builder

from starknet_py.net.client_models import Calls
from ..platform_abc import PlatformABC

@final
class StarknetPlatform(PlatformABC):

    def __init__(self, w_account: WAccount, market: Market, tx_builder: TxBuilder): 
        self._waccount = w_account
        self._market = market
        self._tx_builder = tx_builder

    @staticmethod
    async def from_config(cfg: StrategyConfig) -> "StarknetPlatform":
        platform_cfg = cfg.platform.config
        market_cfg = cfg.market
        w_account = get_wrapped_account(platform_cfg.account)

        market = await get_market(market_cfg.venue, account = w_account, market_id = market_cfg.market_id)
        tx_builder = get_tx_builder(platform_cfg.tx_builder.name, market)

        return StarknetPlatform(
            w_account=w_account,
            market = market,
            tx_builder=tx_builder
        )

    async def initialize_trading(self) -> None:
        await self._market.setup(self._waccount)


    async def execute_operations(self, prologue: list[Calls], ops: ReconciledOrders) -> None:
        await self._tx_builder.build_and_execute_transactions(
            wrapped_account=self._waccount,
            reconciled_orders=ops,
            prologue = prologue
        )

    async def reset(self) -> None:
        await self._waccount.reset_latest_nonce()


    @property
    def market(self) -> Market:
        return self._market