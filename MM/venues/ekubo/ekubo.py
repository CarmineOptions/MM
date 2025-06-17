import math
from decimal import Decimal
from typing import OrderedDict
from typing import TypedDict

import httpx
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.client_models import Calls

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


def get_sqrt_ratio(tick: Decimal) -> Decimal:
    return (Decimal("1.000001").sqrt()**tick) * (Decimal(2)**128)

def tick_to_price(tick: Decimal, token_a_decimals: int, token_b_decimals: int) -> Decimal:
    sqrt_ratio = get_sqrt_ratio(tick)
    # calculate price by formula price = (sqrt_ratio / (2 ** 128)) ** 2 * 10
    # ** (token_a_decimal - token_b_decimal)
    price = ((sqrt_ratio /
                (Decimal(2)**128))**2) * 10**(token_a_decimals - token_b_decimals)
    return price


def price_to_tick(price: Decimal, token_a_decimals: int, token_b_decimals: int) -> int:
    return round(
        math.log(
            (price * Decimal(10) ** (token_b_decimals - token_a_decimals)),
            Decimal('1.000001')
        )
    )

def get_nearest_usable_tick(tick: int, tick_spacing: int) -> int:
    sign = 1 if tick >= 0 else -1
    nearest_tick = sign * round(abs(tick) / tick_spacing) * tick_spacing
    return nearest_tick


class i129(TypedDict):
    mag: int
    sign: bool

class OrderKey(TypedDict):
    token0: int
    token1: int
    tick: i129

def get_order_key(order: FutureOrder | BasicOrder, cfg: EkuboMarketConfig) -> OrderKey:
    # If tick is divisible by 2 * tick_spacing -> selling token0 -> selling base -> Ask order
    # https://github.com/EkuboProtocol/limit-orders-extension/blob/9b9b4db24794013fc8b95daf0935af9ed3f469b6/src/limit_orders.cairo#L11C1-L14C1
    tick_spacing = 256 if order.order_side.lower() == 'ask' else 128
    tick = price_to_tick(
        price = order.price,
        token_a_decimals = cfg.token0.decimals,
        token_b_decimals = cfg.token1.decimals
    )
    tick = get_nearest_usable_tick(tick, tick_spacing)
    return {
        'token0': cfg.token0.address,
        'token1': cfg.token1.address,
        'tick': {
            'mag': abs(tick),
            'sign': tick < 0
        }
    }



def _get_basic_orders(
        orders: list[dict], 
        onchain_orders: list[OrderedDict],
        market_cfg: EkuboMarketConfig
    ) -> list[BasicOrder]:
    
    token_a_decimals = market_cfg.token0.decimals
    token_b_decimals = market_cfg.token1.decimals
        
    basic_orders = []

    for order, onchain_order in zip(orders, onchain_orders):
        key = order['orders'][0]['key']

        price = tick_to_price(Decimal(key['tick']), token_a_decimals, token_b_decimals)
        order_id = order['token_id']

        # If tick is divisible by 2 * tick_spacing -> selling token0 -> selling base -> Ask order
        # https://github.com/EkuboProtocol/limit-orders-extension/blob/9b9b4db24794013fc8b95daf0935af9ed3f469b6/src/limit_orders.cairo#L11C1-L14C1
        side = 'Ask' if (key['tick'] % (2*market_cfg.tick_spacing)) == 0 else 'Bid'

        # We want all the amounts to be in base token
        if side == 'Ask':
            amount = Decimal(order['orders'][0]['amount']) / 10**token_a_decimals
            amount_remaining = Decimal(onchain_order['amount0']) / 10**token_a_decimals
        else:
            amount = Decimal(order['orders'][0]['amount']) / 10**token_b_decimals / price
            amount_remaining = Decimal(onchain_order['amount1']) / 10**token_b_decimals / price
        print(order, onchain_order, sep = '\n', end = '\n\n')
        basic_orders.append(BasicOrder(
            price = price,
            amount = amount,
            amount_remaining = amount_remaining,
            order_id = order_id,
            order_side = side,
            entry_time=0,
            market_id = 0,
            venue='Ekubo'
        ))

    return basic_orders


class EkuboClient:
    address = EKUBO_POSITIONS_ADDRESS
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
            market_cfg: EkuboMarketConfig
    ) -> Calls:
        order_key = get_order_key(order, market_cfg)

        if order.order_side.lower() == 'ask':
            amount = order.amount * 10 ** market_cfg.token0.decimals
            clearing_token = market_cfg.token0.address
        else:
            amount = order.amount * order.price * 10**market_cfg.token1.decimals
            clearing_token = market_cfg.token1.address
        
        transfer_invoke = strk.functions['transfer'].prepare_call(
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