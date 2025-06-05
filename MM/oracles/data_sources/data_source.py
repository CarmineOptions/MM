from abc import ABC, abstractmethod
from decimal import Decimal


class DataSource(ABC):
    """
    Abstract base class for data sources providing price information for trading pairs.
    Methods:
        __init__(base: str, quote: str):
            Initializes the data source for a specific (base, quote) currency pair.
            Must be implemented by subclasses.
        get_price() -> Decimal:
            Asynchronously retrieves the current price for the initialized (base, quote) pair.
            Must be implemented by subclasses.
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
