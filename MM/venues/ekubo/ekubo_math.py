import math
from decimal import Decimal

def get_sqrt_ratio(tick: Decimal) -> Decimal:
    return (Decimal("1.000001").sqrt()**tick) * (Decimal(2)**128)

def tick_to_price(tick: Decimal, token_a_decimals: int, token_b_decimals: int) -> Decimal:
    sqrt_ratio = get_sqrt_ratio(tick)
    # calculate price by formula price = (sqrt_ratio / (2 ** 128)) ** 2 * 10
    # ** (token_a_decimal - token_b_decimal)
    price: Decimal = ((sqrt_ratio / (Decimal(2)**128))**2) * \
        10**(token_a_decimals - token_b_decimals)
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