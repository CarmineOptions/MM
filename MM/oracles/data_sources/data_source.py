from abc import ABC, abstractmethod
from decimal import Decimal
from typing import ClassVar


class DataSource(ABC):
    supported_pairs: ClassVar[list[tuple[str, str]]]

    @abstractmethod
    def __init__(self, base: str, quote: str):
        raise NotImplementedError

    @abstractmethod
    async def get_price(self) -> Decimal:
        """
        Returns a price of `base/quote` pair provided during initialization.
        """
        raise NotImplementedError
