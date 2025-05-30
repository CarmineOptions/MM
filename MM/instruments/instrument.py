
from abc import ABC, abstractmethod


class Instrument(ABC):
    net: str
    symbol: str
    name: str
    decimals: int
    address: str 
    