from dataclasses import dataclass
import asyncio
from decimal import Decimal
import httpx
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.client_models import Calls, Call

from venues.ekubo.ekubo_math import get_nearest_usable_tick, price_to_tick, tick_to_price
from venues.ekubo.ekubo_utils import _get_basic_orders, _positions_to_basic_orders, get_order_key
from marketmaking.order import AllOrders, BasicOrder, FutureOrder, OpenOrders, TerminalOrders
from venues.ekubo.ekubo_market_configs import EkuboMarketConfig

EKUBO_POSITIONS_ADDRESS=0x02e0af29598b407c8716b17f6d2795eca1b471413fa03fb145a5e33722184067

@dataclass
class EkuboPositionMetadata:
    liquidity: int
    lower_bound: int
    upper_bound: int
    tick_spacing: int
    fee: int

class EkuboView:
    def __init__(self, ekubo_positions: Contract) -> None:
        self._positions = ekubo_positions
        self._position_metadata: dict[int, EkuboPositionMetadata] = {}

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

        for order, pos in zip(relevant_positions, fetched_positions):
            if not isinstance(pos, BaseException):
                position_metadata = EkuboPositionMetadata(
                    liquidity = pos[0]['liquidity'],
                    lower_bound = order['bounds']['lower'],
                    upper_bound = order['bounds']['upper'],
                    tick_spacing= int(order['pool_key']['tick_spacing'], 0),
                    fee= int(order['pool_key']['fee'], 0),
                )
                self._position_metadata[order['id']] = position_metadata


        if len(relevant_positions) != len(fetched_positions):
            raise ValueError("EkuboCLMM didn't receive same amount of onchain orders.")

        basic_orders = _positions_to_basic_orders( 
            relevant_positions,
            fetched_positions,# type: ignore
            market_cfg
        )

        return AllOrders( 
            active = OpenOrders.from_list(basic_orders),
            terminal = TerminalOrders.from_list([])
        )
    
    def get_cached_position_metadata(self, order_id: int) -> EkuboPositionMetadata | None:
        liquidity = self._position_metadata.get(order_id)

        if liquidity is not None:
            del self._position_metadata[order_id]

        return liquidity

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
    
    def prep_submit_position_call(
        self,
        order: FutureOrder,
        market_cfg: EkuboMarketConfig,
        base_token_contract: Contract,
        quote_token_contract: Contract,
    ) -> Calls:
        if order.order_side.lower() == 'ask':
            amount = order.amount * 10 ** market_cfg.base_token.decimals
            clearing_token = market_cfg.base_token.address
            transfer_token_contract = base_token_contract
        else:
            amount = order.amount * order.price * 10**market_cfg.quote_token.decimals
            clearing_token = market_cfg.quote_token.address
            transfer_token_contract = quote_token_contract
        

        transfer_call = transfer_token_contract.functions['transfer'].prepare_invoke_v3(
            recipient = self._positions.address,
            amount = int(amount)
        )

        
        lower_bound = price_to_tick(order.price, market_cfg.base_token.decimals, market_cfg.quote_token.decimals)
        lower_bound = get_nearest_usable_tick(lower_bound, market_cfg.tick_spacing)
        upper_bound = lower_bound + market_cfg.tick_spacing

        if upper_bound > lower_bound:
            bounds = {
                'upper': {
                    'mag': abs(upper_bound),
                    'sign': upper_bound < 0
                },
                'lower': {
                    'mag': abs(lower_bound),
                    'sign': lower_bound < 0
                }
            }
        else: 
            bounds = {
                'lower': {
                    'mag': abs(upper_bound),
                    'sign': upper_bound < 0
                },
                'upper': {
                    'mag': abs(lower_bound),
                    'sign': lower_bound < 0
                }
            }

        deposit_call = self._positions.functions['mint_and_deposit'].prepare_invoke_v3(
            pool_key = {
                'token0': market_cfg.base_token.address,
                'token1': market_cfg.quote_token.address,
                'fee': market_cfg.fee,
                'tick_spacing': market_cfg.tick_spacing,
                'extension': 0
            },
            bounds = bounds,
            min_liquidity = 0
        )

        clear_call = self._positions.functions['clear'].prepare_invoke_v3(
            token = {
                'contract_address': clearing_token
            }
        )

        return [
            transfer_call,
            deposit_call,
            clear_call
        ]
    
    def prep_remove_position_call(self, order: BasicOrder, cfg: EkuboMarketConfig) -> Call:
        metadata = self.view.get_cached_position_metadata(order.order_id)

        if metadata is None: 
            raise ValueError(f"No liquidity found for EkuboCLMM order: {order}")
            
        return self._prep_remove_position_call_with_metadata(
            order = order,
            cfg = cfg,
            metadata = metadata
        )
    
    def _prep_remove_position_call_with_metadata(self, order: BasicOrder, cfg: EkuboMarketConfig, metadata: EkuboPositionMetadata) -> Call:
        pool_key = pool_key = {
            'token0': cfg.base_token.address,
            'token1': cfg.quote_token.address,
            'fee': metadata.fee,
            'tick_spacing': metadata.tick_spacing,
            'extension': 0
        }


        # lower_bound = price_to_tick(order.price, 18, 6)
        # upper_bound = lower_bound + cfg.tick_spacing
        # upper_bound_price = tick_to_price(Decimal(upper_bound), 18, 6)

        # if upper_bound_price > order.price:
        #     bounds = {
        #         'lower': {
        #             'mag': abs(lower_bound),
        #             'sign': lower_bound < 0
        #         },
        #         'upper': {
        #             'mag': abs(upper_bound),
        #             'sign': upper_bound < 0
        #         }
        #     }
        # else:
        #     bounds = {
        #         'upper': {
        #             'mag': abs(lower_bound),
        #             'sign': lower_bound < 0
        #         },
        #         'lower': {
        #             'mag': abs(upper_bound),
        #             'sign': upper_bound < 0
        #         }
        #     }

        bounds = {
            'upper': {
                'mag': abs(metadata.upper_bound),
                'sign': metadata.upper_bound < 0
            },
            'lower': {
                'mag': abs(metadata.lower_bound),
                'sign': metadata.lower_bound < 0
            }
        }

        return self._positions.functions['withdraw'].prepare_invoke_v3(
            id = order.order_id,
            pool_key = pool_key,
            bounds = bounds,
            liquidity = metadata.liquidity,
            min_token0 = 0,
            min_token1 = 0,
            collect_fees = True
        )

    
    def prep_delete_maker_order_call(self, order: BasicOrder, cfg: EkuboMarketConfig) -> Call:
        order_key = get_order_key(order, cfg)
        return self._positions.functions['close_limit_order'].prepare_invoke_v3(
            id = order.order_id,
            order_key = order_key
        )