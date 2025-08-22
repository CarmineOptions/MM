from dataclasses import dataclass
from decimal import Decimal


from marketmaking.order import AllOrders

@dataclass
class PositionInfo:
    '''
    Represents the position information for a market, including balances, withdrawable amounts, and amounts in orders.
    This class provides properties to calculate the total base and quote amounts of position.
    '''
    balance_base: Decimal
    balance_quote: Decimal

    withdrawable_base: Decimal
    withdrawable_quote: Decimal

    in_orders_base: Decimal
    in_orders_quote: Decimal

    @property
    def total_base(self) -> Decimal:
        return self.balance_base + self.withdrawable_base + self.in_orders_base

    @property
    def total_quote(self) -> Decimal:
        return self.balance_quote + self.withdrawable_quote + self.in_orders_quote

    @staticmethod
    def empty() -> "PositionInfo":
        return PositionInfo(
            balance_base=Decimal(0),
            balance_quote=Decimal(0),
            withdrawable_base=Decimal(0),
            withdrawable_quote = Decimal(0),
            in_orders_base=Decimal(0),
            in_orders_quote=Decimal(0),
        )

@dataclass(frozen=True)
class AccountState:
    position: PositionInfo
    orders: AllOrders
