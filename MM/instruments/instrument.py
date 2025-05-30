
from abc import ABC, abstractmethod


class Instrument(ABC):
    @property
    @abstractmethod
    def net(self) -> str:
        """
        Defines where the token/asset/instrument is traded.
        Eg. Starknet, Binance ... 
        """
        pass

    @property
    @abstractmethod
    def symbol(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def decimals(self) -> int:
        pass

    @property
    @abstractmethod
    def address(self) -> str | None:
        pass

    
    
