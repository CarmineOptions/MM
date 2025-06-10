from decimal import Decimal
import logging
from typing import Any, TypedDict

from marketmaking.order import BasicOrder
from marketmaking.market import Market

class MyOrders(TypedDict):
    bids: list[BasicOrder]
    asks: list[BasicOrder]

class StateMarket:
    # TODO: Add orderbook functionalities
    # TODO: Add account info
    # TODO: During initialization add all the data fetchers and update inside of the class
    #       instead of passing update data
    
    def __init__(self, market: Market) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._logger.info("Initializing StateMarket")

        self.market: Market = market

        self.oracle: Decimal | None = None

        self.my_orders: MyOrders = {
            'asks': [],
            'bids': []
        }

    def update(self, data: dict[str, Any]) -> None:
        """
        Update the state with new data.
        :param data: New data to be added to the state.
        """
        self._logger.debug("Updating state with data: %s", data)

        if data["type"] == "custom_oracle":
            self.oracle = data["data"]
        elif data["type"] == "my_orders_snapshot":
            self.my_orders['asks'] = data["data"]['asks']
            self.my_orders['bids'] = data["data"]['bids']
        else:
            raise NotImplementedError(f"Unknown data type: {data['type']}")

