from typing import Dict, List
import logging

from marketmaking.market import Market
from marketmaking.order import Order
from marketmaking.waccount import WAccount



class TODO:
    """TODO: Placeholder for the actual class definition.
    This should be replaced with the actual class that is being used in the code.
    """
    pass


class StateMarket:

    def __init__(self, accounts: List[WAccount], market: Market) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._logger.info('Initializing StateMarket')

        self.market: Market = market
        # Visible on-chain orderbook.
        self.orderbook: TODO = None
        self.orderbook_initialized: bool = False
        self.non_processed_event_queue: List[TODO] = []

        self.oracle: TODO = None

        # Trades that are visible on-chain and L2 accepted
        self.trades: List[TODO] = []
        # Trades that are pending.
        self.pending_trades: List[TODO] = []

        self.my_orders: Dict[str, Order] = {account.address: [] for account in accounts}
        self.pending_orders: Dict[str, Order] = {account.address: [] for account in accounts}
        self.my_inflight_orders: Dict[str, Order] = {account.address: [] for account in accounts}


    def update(self, data: TODO) -> None:
        """
        Update the state with new data.
        :param data: New data to be added to the state.
        """
        self._logger.debug('Updating state with data: %s', data)

        if data['type'] == 'custom_oracle':
            self.oracle = data['data']
        elif data['type'] == 'pending_order':
            self.pending_orders[data['account']].append(data['data'])
        elif data['type'] == 'my_orders_snapshot':
            self.my_orders[data['account']] = data['data']
        else:
            raise NotImplementedError(f"Unknown data type: {data['type']}")


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
