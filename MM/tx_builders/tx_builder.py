
from abc import ABC, abstractmethod

from marketmaking.waccount import WAccount
from markets.market import Market
from marketmaking.reconciling.order_reconciler import ReconciledOrders

# TODO: Not only builds the txs but also executes them
#       so consider some other name 

class TxBuilder(ABC):
    '''
    Abstract base class for transaction builders in the market making system.
    This class defines the interface for building and executing transactions.
    '''

    @abstractmethod
    def __init__(self, market: Market) -> None:
        # TODO: Add max fees
        raise NotImplementedError

    @abstractmethod
    async def build_and_execute_transactions(
        self, 
        account: WAccount, 
        reconciled_orders: ReconciledOrders
    ) -> None:
        '''       
        Build and execute transactions based on the reconciled orders.
        '''       
        # TODO:Add prologue and epilogue
        # NOTE: Currently takes in orders and creates the calls from them
        #       once needed it will just take in the calls directly
        raise NotImplementedError


    


