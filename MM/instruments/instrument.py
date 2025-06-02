
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

class Instrument(ABC):
    net: str
    symbol: str
    name: str
    decimals: int
    address: str 

@dataclass
class InstrumentAmount:
    instrument: Instrument
    amount_raw: int
    
    @property
    def amount_hr(self) -> Decimal:
        return Decimal(self.amount_raw) / 10 ** self.instrument.decimals
    