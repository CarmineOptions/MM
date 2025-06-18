
import httpx
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.client_models import Calls

from venues.ekubo.ekubo_utils import _get_basic_orders, get_order_key
from marketmaking.order import BasicOrder, FutureOrder
from venues.ekubo.ekubo_market_configs import EkuboMarketConfig

EKUBO_POSITIONS_ADDRESS=0x02e0af29598b407c8716b17f6d2795eca1b471413fa03fb145a5e33722184067

class EkuboView:
    def __init__(self, ekubo_positions: Contract) -> None:
        self._positions = ekubo_positions

    @staticmethod
    async def from_provider(provider: Account | FullNodeClient) -> "EkuboView":
        positions = await Contract.from_address(address=EKUBO_POSITIONS_ADDRESS, provider=provider)
        return EkuboView(ekubo_positions=positions)
    
    async def get_active_orders(
            self,
            wallet: int,
            market_cfg: EkuboMarketConfig
        ) -> list[BasicOrder]:
        url = f'https://starknet-mainnet-api.ekubo.org/limit-orders/orders/{hex(wallet)}?showClosed=false'
        
        async with httpx.AsyncClient() as client:
            orders_resp = await client.get(url)
        
        orders_resp.raise_for_status()
        orders = orders_resp.json()['orders']

        
        orders = [
            o for o in orders
            if int(o['orders'][0]['key']['token0'], 0) == market_cfg.token0.address
            and
            int(o['orders'][0]['key']['token1'], 0) == market_cfg.token1.address
        ]

        onchain_calldata = [
            (
                o['token_id'],
                {
                    'token0': int(o['orders'][0]['key']['token0'], 0),
                    'token1': int(o['orders'][0]['key']['token1'], 0),
                    'tick' : {
                        'mag': abs(o['orders'][0]['key']['tick']),
                        'sign': o['orders'][0]['key']['tick'] < 0
                    }
                }   
            )
            for o in orders
        ]

        onchain_orders = await self._positions.functions['get_limit_orders_info'].call(
            params = onchain_calldata
        )

        if len(onchain_orders[0]) != len(orders):
            raise ValueError('Ekubo orders missing')
        
        basic_orders = _get_basic_orders(
            orders = orders,
            onchain_orders=onchain_orders[0],
            market_cfg = market_cfg
        )

        return basic_orders


class EkuboClient:
    def __init__(self, ekubo_positions: Contract) -> None:
        self._positions = ekubo_positions
        self.view = EkuboView(ekubo_positions=self._positions)

    @staticmethod
    async def from_account(account: Account) -> "EkuboClient":
        positions = await Contract.from_address(address = EKUBO_POSITIONS_ADDRESS, provider = account)
        return EkuboClient(ekubo_positions=positions)
    

    def prep_submit_maker_order_call(
            self,
            order: FutureOrder,
            market_cfg: EkuboMarketConfig,
            base_token_contract: Contract,
            quote_token_contract: Contract,
    ) -> Calls:
        order_key = get_order_key(order, market_cfg)
        print(order_key)
        if order.order_side.lower() == 'ask':
            amount = order.amount * 10 ** market_cfg.token0.decimals
            clearing_token = market_cfg.token0.address
            transfer_token = base_token_contract
        else:
            amount = order.amount * order.price * 10**market_cfg.token1.decimals
            clearing_token = market_cfg.token1.address
            transfer_token = quote_token_contract
        
        transfer_invoke = transfer_token.functions['transfer'].prepare_invoke_v3(
            amount = int(amount),
            recipient = self.view._positions.address
        )

        swap_invoke = self._positions.functions['swap_to_limit_order_price_and_maybe_mint_and_place_limit_order'].prepare_invoke_v3(
            order_key = order_key,
            amount = int(amount)
        )

        clear_invoke = self._positions.functions['clear'].prepare_invoke_v3(
            token = {
                'contract_address': clearing_token
            }
        )

        return [
            transfer_invoke,
            swap_invoke,
            clear_invoke
        ]
    
    def prep_delete_maker_order_call(self, order: BasicOrder, cfg: EkuboMarketConfig) -> Calls:
        order_key = get_order_key(order, cfg)
        return self._positions.functions['close_limit_order'].prepare_invoke_v3(
            id = order.order_id,
            order_key = order_key
        )