import logging
from typing import Any

from marketmaking.market import Market
from marketmaking.waccount import WAccount


class TODO:
    """TODO: Placeholder for the actual class definition.
    This should be replaced with the actual class that is being used in the code.
    """

    pass


class StateMarket:
    def __init__(self, accounts: list[WAccount], market: Market) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._logger.info("Initializing StateMarket")

        self.market: Market = market
        # Visible on-chain orderbook.
        self.orderbook = None
        self.orderbook_initialized: bool = False
        self.non_processed_event_queue: list[TODO] = []

        self.oracle = None

        # Trades that are visible on-chain and L2 accepted
        # TODO: Use this
        # self.trades: List[TODO] = []
        # Trades that are pending.
        # TODO: Use this
        # self.pending_trades: List[TODO] = []

        self.my_orders: dict[int, dict[str, Any]] = {account.address: {} for account in accounts}

        # TODO: Use these
        # self.pending_orders: dict[int, dict] = {account.address: [] for account in accounts}
        # self.my_inflight_orders: dict[int, list[BasicOrder]] = {account.address: [] for account in accounts}

    def update(self, data: dict[str, Any]) -> None:
        """
        Update the state with new data.
        :param data: New data to be added to the state.
        """
        self._logger.debug("Updating state with data: %s", data)

        if data["type"] == "custom_oracle":
            self.oracle = data["data"]
        elif data["type"] == "my_orders_snapshot":
            self.my_orders[data["account"]] = data["data"]
        else:
            raise NotImplementedError(f"Unknown data type: {data['type']}")

        # elif data['type'] == 'pending_order':
        #     TODO: Use this
        #     self.pending_orders[data['account']].append(data['data'])

    def initialize_orderbook(self) -> None:
        """
        Initialize the orderbook.
        This method should be called to start or restart the orderbook process.
        """
        pass
        # Make sure there will be no gap between orderbook snapshot and non-processed events.

        # block_number_event = max(x.block_number for x in self.non_processed_event_queue if x.block_number is not None)

        # orderbook =

        # self.orderbook_initialized = True
