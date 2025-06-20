from abc import ABC
from dataclasses import dataclass
from decimal import Decimal


class Instrument(ABC):
    '''
    Base class for all instruments (e.g., tokens, coins).
    '''
    platform: str
    symbol: str
    name: str
    decimals: int
    address: int


@dataclass(frozen=True)
class InstrumentAmount:
    '''
    Represents an amount of an Instrument, with raw and human-readable values.
    '''
    instrument: Instrument
    amount_raw: int

    @property
    def amount_hr(self) -> Decimal:
        amt_raw = Decimal(self.amount_raw)
        multiplier = Decimal(10**self.instrument.decimals)
        return amt_raw / multiplier
