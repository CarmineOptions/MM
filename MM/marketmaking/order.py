from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class BasicOrder:
    """
    Simple class representing on-chain order. 
    All values are expected to be in "raw" form.
    """
    price: Decimal
    amount: Decimal
    amount_remaining: Decimal

    order_id: int
    market_id: int

    order_side: str
    entry_time: int


    @staticmethod
    def from_remus_order(o: dict) -> "BasicOrder":
        return BasicOrder(
            price = Decimal(o['price']),
            amount = Decimal(o['amount']),
            amount_remaining = Decimal(o['amount_remaining']),
            order_id = int(o['maker_order_id']),
            market_id= int(o['market_id']),
            order_side = o['order_side'].variant,
            entry_time = int(o['entry_time'])
        )


@dataclass
class FutureOrder:
    """
    Class representing an order that will be sent to the chain.
    """
    order_side: str # TODO: use Literal or enum here
    amount: int
    price: int

