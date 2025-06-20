from abc import ABC, abstractmethod
from decimal import Decimal


class DataSource(ABC):
    """
    Abstract base class for data sources providing price information for trading pairs.
    """

    @abstractmethod
    def __init__(self, base: str, quote: str):
        raise NotImplementedError

    @abstractmethod
    async def get_price(self) -> Decimal:
        """
        Returns a price of `base/quote` pair provided during initialization.
        """
        raise NotImplementedError
