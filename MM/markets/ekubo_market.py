import logging
from typing import final

from starknet_py.net.client_models import Calls
from starknet_py.contract import Contract

from MM.marketmaking.market import PositionInfo
from marketmaking.order import BasicOrder, FutureOrder
from marketmaking.waccount import WAccount
from markets.market import Market
from venues.ekubo.ekubo import EkuboClient
from venues.ekubo.ekubo_market_configs import EkuboMarketConfig


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

    async def setup(self, wrapped_account: WAccount) -> None:
        pass

    async def get_current_orders(self) -> list[BasicOrder]:
        return await self._client.view.get_active_orders(
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
        raise NotImplementedError

    
    
