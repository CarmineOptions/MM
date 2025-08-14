import logging

from decimal import Decimal
from typing import Any, OrderedDict, TypedDict

from marketmaking.order import BasicOrder, FutureOrder
from venues.ekubo.ekubo_market_configs import EkuboMarketConfig
from venues.ekubo.ekubo_math import get_nearest_usable_tick, price_to_tick, tick_to_price


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
        token_a_decimals = cfg.base_token.decimals,
        token_b_decimals = cfg.quote_token.decimals
    )
    tick = get_nearest_usable_tick(tick, tick_spacing)

    if order.is_bid() and tick % 256 == 0:
        tick = tick - 128

    return {
        'token0': cfg.base_token.address,
        'token1': cfg.quote_token.address,
        'tick': {
            'mag': abs(tick),
            'sign': tick < 0
        }
    }


def _get_basic_orders(
        orders: list[dict[str, Any]], 
        onchain_orders: list[OrderedDict[str, Any]],
        market_cfg: EkuboMarketConfig
    ) -> list[BasicOrder]:
    
    token_a_decimals = market_cfg.base_token.decimals
    token_b_decimals = market_cfg.quote_token.decimals
        
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
        basic_orders.append(BasicOrder(
            price = price,
            amount = amount,
            amount_remaining = amount_remaining,
            order_id = order_id,
            order_side = side,
            entry_time=0,
            market_id = 0,
            venue='EkuboLO'
        ))

    return basic_orders


def _positions_to_basic_orders(api_orders: list[dict], onchain_orders: list[dict | BaseException], market_cfg: EkuboMarketConfig) -> list[BasicOrder]: # type: ignore
    token_a_decimals = market_cfg.base_token.decimals
    token_b_decimals = market_cfg.quote_token.decimals
        
    basic_orders = []

    for order, onchain_order in zip(api_orders, onchain_orders):
        if isinstance(onchain_order, BaseException):
            logging.error("")
            continue
        
        onchain_order = onchain_order[0]
        
        order_id = order['id']
        pool_price_tick = onchain_order['pool_price']['tick']
        pool_price = -pool_price_tick['mag'] if pool_price_tick['sign'] else pool_price_tick['mag']
        pool_price = tick_to_price(pool_price, token_a_decimals, token_b_decimals)

        order_bounds = order['bounds']
        # Order price is kinda wrong, but good enough for very low tick sizes
        order_price = tick_to_price(
            min(order_bounds['lower'], order_bounds['upper']), market_cfg.base_token.decimals, market_cfg.quote_token.decimals
        )

        base_amount = Decimal(onchain_order['amount0']) / 10 ** token_a_decimals
        quote_amount = Decimal(onchain_order['amount1']) / 10 ** token_b_decimals
        total_base_amount = base_amount + quote_amount / order_price

        base_fees = Decimal(onchain_order['fees0']) / 10 ** token_a_decimals
        quote_fees = Decimal(onchain_order['fees1']) / 10 ** token_b_decimals
        total_base_fees = base_fees + quote_fees

        total_base_position = total_base_amount + total_base_fees

        is_bid = pool_price > order_price

        basic_orders.append(
            BasicOrder(
                price = order_price,
                amount = total_base_position,
                amount_remaining = total_base_position,
                order_id = order_id,

                order_side = 'Bid' if is_bid else 'Ask',
                entry_time=0,
                market_id=market_cfg.market_id,
                venue = 'EkuboCLMM'
            )
        )


    return basic_orders