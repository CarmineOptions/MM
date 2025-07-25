
import asyncio
import httpx
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.client_models import Calls, Call

from venues.ekubo.ekubo_utils import _get_basic_orders, _positions_to_basic_orders, get_order_key
from marketmaking.order import AllOrders, BasicOrder, FutureOrder, OpenOrders, TerminalOrders
from venues.ekubo.ekubo_market_configs import EkuboMarketConfig

EKUBO_POSITIONS_ADDRESS=0x02e0af29598b407c8716b17f6d2795eca1b471413fa03fb145a5e33722184067

class EkuboView:
    def __init__(self, ekubo_positions: Contract) -> None:
        self._positions = ekubo_positions

    @staticmethod
    async def from_provider(provider: Account | FullNodeClient) -> "EkuboView":
        positions = await Contract.from_address(address=EKUBO_POSITIONS_ADDRESS, provider=provider)
        return EkuboView(ekubo_positions=positions)
    
    async def get_all_limit_orders(
            self,
            wallet: int,
            market_cfg: EkuboMarketConfig
        ) -> AllOrders:
        url = f'https://starknet-mainnet-api.ekubo.org/limit-orders/orders/{hex(wallet)}?showClosed=false'
        
        async with httpx.AsyncClient() as client:
            orders_resp = await client.get(url)
        
        orders_resp.raise_for_status()
        orders = orders_resp.json()['orders']

        
        orders = [
            o for o in orders
            if int(o['orders'][0]['key']['token0'], 0) == market_cfg.base_token.address
            and
            int(o['orders'][0]['key']['token1'], 0) == market_cfg.quote_token.address
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

        active_orders = []
        terminal_orders = []

        for order in basic_orders:
            if order.amount_remaining == 0:
                terminal_orders.append(order)
                continue

            active_orders.append(order)

        return AllOrders(
            active = OpenOrders.from_list(active_orders),
            terminal = TerminalOrders.from_list(terminal_orders)
        )
    
    
    async def get_all_clmm_positions_as_limit_orders(
            self,
            wallet: int,
            market_cfg: EkuboMarketConfig
        ) -> AllOrders:

        url = f'https://mainnet-api.ekubo.org/positions/{hex(wallet)}?showClosed=false'

        async with httpx.AsyncClient() as client:
            positions_resp = await client.get(url)

        positions_resp.raise_for_status()
        positions = positions_resp.json()['data']
        
        relevant_positions = [
            p for p in positions
            if int(p['pool_key']['token0'], 0) == market_cfg.base_token.address
            and
            int(p['pool_key']['token1'], 0) == market_cfg.quote_token.address
        ]

        tasks = []

        for onchain_p in relevant_positions:
            lower_tick = onchain_p['bounds']['lower']
            upper_tick = onchain_p['bounds']['upper']

            bounds = {
                'lower' : {
                    'mag': abs(lower_tick),
                    'sign': lower_tick < 0
                },
                'upper' : {
                    'mag': abs(upper_tick),
                    'sign': upper_tick < 0
                }
            }
            tasks.append(
                self._positions.functions['get_token_info'].call(
                    id = onchain_p['id'],
                    pool_key = {
                        k: int(v, 0) for k, v in onchain_p['pool_key'].items()
                    },
                    bounds = bounds
                )
            )

        fetched_positions = await asyncio.gather(*tasks, return_exceptions=True)

        if len(relevant_positions) != len(fetched_positions):
            raise ValueError(f"EkuboCLMM didn't receive same amount of onchain orders.")

        basic_orders = _positions_to_basic_orders(
            relevant_positions,
            fetched_positions,
            market_cfg
        )

        return AllOrders(
            active = OpenOrders.from_list(basic_orders),
            terminal = TerminalOrders.from_list([])
        )

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
        if order.order_side.lower() == 'ask':
            amount = order.amount * 10 ** market_cfg.base_token.decimals
            clearing_token = market_cfg.base_token.address
            transfer_token_contract = base_token_contract
        else:
            amount = order.amount * order.price * 10**market_cfg.quote_token.decimals
            clearing_token = market_cfg.quote_token.address
            transfer_token_contract = quote_token_contract
        
        transfer_invoke = transfer_token_contract.functions['transfer'].prepare_invoke_v3(
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
    
    def prep_delete_maker_order_call(self, order: BasicOrder, cfg: EkuboMarketConfig) -> Call:
        order_key = get_order_key(order, cfg)
        return self._positions.functions['close_limit_order'].prepare_invoke_v3(
            id = order.order_id,
            order_key = order_key
        )