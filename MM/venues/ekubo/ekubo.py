
from decimal import Decimal
from typing import OrderedDict

import httpx
from starknet_py.contract import Contract

from MM.marketmaking.order import BasicOrder


def get_sqrt_ratio(tick: Decimal) -> Decimal:
    return (Decimal("1.000001").sqrt()**tick) * (Decimal(2)**128)

def tick_to_price(tick: Decimal, token_a_decimals: int, token_b_decimals: int) -> Decimal:
    sqrt_ratio = get_sqrt_ratio(tick)
    # calculate price by formula price = (sqrt_ratio / (2 ** 128)) ** 2 * 10
    # ** (token_a_decimal - token_b_decimal)
    price = ((sqrt_ratio /
                (Decimal(2)**128))**2) * 10**(token_a_decimals - token_b_decimals)
    return price

def _get_basic_orders(
        orders: list[dict], 
        onchain_orders: list[OrderedDict],
        token_a_decimals: int,
        token_b_decimals: int,
        tick_spacing: int
        ) -> list[BasicOrder]:
    basic_orders = []

    for order, onchain_order in zip(orders, onchain_orders):
        key = order['orders'][0]['key']

        price = tick_to_price(Decimal(key['tick']), token_a_decimals, token_b_decimals)
        order_id = order['token_id']

        # If tick is divisible by 2 * tick_spacing -> selling token0 -> selling base -> Ask order
        # https://github.com/EkuboProtocol/limit-orders-extension/blob/9b9b4db24794013fc8b95daf0935af9ed3f469b6/src/limit_orders.cairo#L11C1-L14C1
        side = 'Ask' if (key['tick'] % (2*tick_spacing)) == 0 else 'Bid'

        # We want all the amounts to be in base token
        if side == 'Ask':
            amount = Decimal(order['orders'][0]['amount']) / 10**token_a_decimals
            amount_remaining = Decimal(onchain_order['amount0']) / 10**token_a_decimals
        else:
            amount = Decimal(order['orders'][0]['amount']) / 10**token_b_decimals / price
            amount_remaining = Decimal(onchain_order['amount1']) / 10**token_b_decimals / price

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

async def get_active_orders(
        wallet: int,
        ekubo_positions: Contract,
        token0: int,
        token1: int,
        token_a_decimals: int,
        token_b_decimals: int,
        tick_spacing: int
    ) -> list[BasicOrder]:
    url = f'https://starknet-mainnet-api.ekubo.org/limit-orders/orders/{wallet}?showClosed=false'
    
    async with httpx.AsyncClient() as client:
        orders_resp = await client.get(url)
    
    orders_resp.raise_for_status()
    orders = orders_resp.json()['orders']
    
    orders = [
        o for o in orders
        if int(o['orders'][0]['key']['token0'], 0) == token0
        and
        int(o['orders'][0]['key']['token1'], 0) == token1
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

    onchain_orders = await ekubo_positions.functions['get_limit_orders_info'].call(
        params = onchain_calldata
    )

    if len(onchain_orders[0]) != len(orders):
        raise ValueError('Ekubo orders missing')
    
    basic_orders = _get_basic_orders(
        orders = orders,
        onchain_orders=onchain_orders[0],
        token_a_decimals=token_a_decimals,
        token_b_decimals=token_b_decimals,
        tick_spacing=tick_spacing
    )   

    return basic_orders