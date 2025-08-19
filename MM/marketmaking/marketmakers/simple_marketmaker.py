from decimal import Decimal
import logging

from monitoring import metrics
from markets.market import Market, PrologueOps, PrologueOp_SeekLiquidity
from marketmaking.orderchain.order_chain import OrderChain
from marketmaking.reconciling.order_reconciler import OrderReconciler, ReconciledOrders
from state.state import State

MAX_UINT = 2**256 - 1


class SimpleMarketMaker:
    """
    Simple MarketMaker that makes market on single pair using single account.
    """

    def __init__(
        self,
        market: Market,
        order_reconciler: OrderReconciler,
        order_chain: OrderChain,
    ):
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._logger.info("Initializing MarketMaker")

        self.market = market
        self.order_reconciler = order_reconciler
        self.order_chain = order_chain

    def get_prologue(self, state: State) -> list[PrologueOps]:
        return [PrologueOp_SeekLiquidity(Decimal("inf"))]

    async def pulse(self, state: State) -> tuple[list[PrologueOps], ReconciledOrders]:

        prologue = self.get_prologue(state=state)
        
        desired_orders = self.order_chain.process(state)

        reconciled = self.order_reconciler.reconcile(
            existing_orders=state.account.orders.active, 
            state=state, 
            desired_orders=desired_orders
        )

        metrics.track_quoted_info(
            orders = reconciled,
            fair_price = state.fair_price
 
        )
        return prologue, reconciled
