from abc import ABC
from dataclasses import dataclass
from decimal import Decimal


class Instrument(ABC):
    platform: str
    symbol: str
    name: str
    decimals: int
    address: int


@dataclass
class InstrumentAmount:
    instrument: Instrument
    amount_raw: int

    @property
    def amount_hr(self) -> Decimal:
        amt_raw = Decimal(self.amount_raw)
        multiplier = Decimal(10**self.instrument.decimals)
        return amt_raw / multiplier
