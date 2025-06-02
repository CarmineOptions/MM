from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class BasicOrder:
    """
    Simple class representing on-chain order. 
    All values are expected to be in "human-readable" form.
    """
    price: Decimal
    amount: Decimal
    amount_remaining: Decimal

    order_id: int
    market_id: int

    order_side: str
    entry_time: int

    platform: str
    venue: str

    # TODO: Add info regarding instruments here too, or use InstrumentAmount


@dataclass
class FutureOrder:
    """
    Class representing an order that will be sent to the chain.
    """
    order_side: str # TODO: use Literal or enum here
    amount: int
    price: int

