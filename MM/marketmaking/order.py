from dataclasses import dataclass
from decimal import Decimal


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

    venue: str

    # TODO: Add info regarding instruments here too, or use InstrumentAmount

    def is_bid(self) -> bool:
        return self.order_side.lower() == "bid"


@dataclass(frozen=True)
class FutureOrder:
    """
    Class representing an order that will be sent to the chain. Should always be in human-readable form
    """

    order_side: str 
    amount: Decimal
    price: Decimal
    platform: str
    venue: str
    
    def is_bid(self) -> bool:
        return self.order_side.lower() == "bid"


@dataclass(frozen=True)
class OpenOrders:
    """
    Class that holds lists of bids and asks.
    These orders are active and not expired or fully matched.
    """

    bids: list[BasicOrder]
    asks: list[BasicOrder]

    @property
    def all_orders(self) -> list[BasicOrder]:
        return self.bids + self.asks

    @staticmethod
    def from_list(orders: list[BasicOrder]) -> "OpenOrders":
        """
        Constructs lists of OpenOrders from list of BasicOrder, separating
        them into *sorted* bids and asks.

        Doesn't check if they are all from the same market/venue...
        """

        bids: list[BasicOrder] = []
        asks: list[BasicOrder] = []

        for o in orders:
            if o.order_side.lower() == "bid":
                bids.append(o)
                continue

            asks.append(o)

        bids = sorted(bids, key=lambda x: -x.price)
        asks = sorted(asks, key=lambda x: -x.price)

        return OpenOrders(bids=bids, asks=asks)

@dataclass(frozen=True)
class TerminalOrders:
    '''
    Class that  holds lists of bids and asks.
    These orders are either fully matched or expired or just 
    inactive in some other way
    '''

    bids: list[BasicOrder]
    asks: list[BasicOrder]

    @property
    def all_orders(self) -> list[BasicOrder]:
        return self.bids + self.asks
    
    @staticmethod
    def from_list(orders: list[BasicOrder]) -> "TerminalOrders":
        """
        Constructs lists of OpenOrders from list of BasicOrder, separating
        them into *sorted* bids and asks.

        Doesn't check if they are all from the same market/venue...
        """

        bids: list[BasicOrder] = []
        asks: list[BasicOrder] = []

        for o in orders:
            if o.order_side.lower() == "bid":
                bids.append(o)
                continue

            asks.append(o)

        bids = sorted(bids, key=lambda x: -x.price)
        asks = sorted(asks, key=lambda x: -x.price)

        return TerminalOrders(bids=bids, asks=asks)

@dataclass
class AllOrders:
    '''
    Class that holds all orders, both active and terminal.
    This is used to represent the state of all orders in the market.
    '''
    active: OpenOrders
    terminal: TerminalOrders


@dataclass
class DesiredOrders:
    '''
    Class that holds lists of future orders that should be sent to the chain.
    These orders are not yet on-chain, but are desired to be sent.
    '''
    bids: list[FutureOrder]
    asks: list[FutureOrder]

    @property
    def all_orders(self) -> list[FutureOrder]:
        return self.bids + self.asks
