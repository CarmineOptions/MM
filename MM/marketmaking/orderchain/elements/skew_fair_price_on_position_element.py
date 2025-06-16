


from decimal import Decimal
import logging
from typing import final
from marketmaking.orderchain.elements.element import OrderChainElement
from marketmaking.order import DesiredOrders
from state.state import State

@final
class SkewFairPriceOnPositionElement(OrderChainElement):
    """
    This element skews the fair price based on the position imbalance.
    It calculates the imbalance between the base and quote value of the position,
    and adjusts the fair price accordingly. The adjustment is done by a percentage
    defined by the `bias` parameter, which indicates how much to move the fair price
    per one unit of position imbalance. The adjustment is capped by the
    `max_skew` parameter, which limits the maximum skewing effect.
    Attributes:
        bias (Decimal): Price adjustment applied per unit of normalized imbalance [-1.0, 1.0].
        max_skew (Decimal): The maximum skew allowed for the fair price.  

    Note:
        This element should go before any order-generating ones in order to adjust the fair price for 
        the following elements.
    """

    def __init__(self, bias: Decimal, max_skew: Decimal) -> None:
        # What percentage to move the FP per percentage of imbalance
        self.bias = bias
        self.max_skew = max_skew

    def process(self, state: State, orders: DesiredOrders) -> DesiredOrders:

        fair_price = state.fair_price

        # Base is in base units, quote in quote units
        base = state.account.position.total_base
        quote = state.account.position.total_quote

        base_value = base * fair_price
        quote_value = quote
        total_value = base_value + quote_value
        if total_value == 0:
            return orders

        # If base value is higher we want to sell more so 
        # we need to shift the price lower to make asks more aggressive
        imbalance = ((quote_value - base_value ) / (base_value + quote_value))

        logging.info(f"Current imbalance: {imbalance}")
        
        price_shift_perc = imbalance * self.bias
        price_shift_perc = max(
            -self.max_skew, min(price_shift_perc, self.max_skew)
        )

        logging.info(f"Current price shift: {price_shift_perc}")

        new_fair_price = fair_price * (1 + price_shift_perc)

        # Set new fair price
        # Logging is done in the setter of the fair price
        state.fair_price = new_fair_price

        return orders
