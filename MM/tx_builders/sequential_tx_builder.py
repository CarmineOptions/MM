import asyncio
import logging
from typing import final

from platforms.starknet.starknet_account import WAccount
from marketmaking.reconciling.order_reconciler import ReconciledOrders
from markets.market import StarknetMarketABC
from marketmaking.order import BasicOrder, FutureOrder
from monitoring import metrics
from .tx_builder import TxBuilder
from starknet_py.net.client_models import Calls

@final
class SequentialTransactionBuilder(TxBuilder):
    """Class to build transactions for the market maker.
    This class is responsible for creating and executing transactions
    that will be sent to the blockchain for execution.

    This is a simple TxBuilder that executes all 
    """

    def __init__(
        self,
        market: StarknetMarketABC,
    ) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._logger.info("Initializing TransactionBuilder")

        self.market = market

    async def build_and_execute_transactions(
        self,
        wrapped_account: WAccount,
        reconciled_orders: ReconciledOrders,
        prologue: list[Calls]
    ) -> None:
        await self.execute_prologue(
            calls = prologue,
            wrapped_account = wrapped_account
        )       

        await self.delete_quotes(
            to_be_canceled=reconciled_orders.to_cancel,
            wrapped_account=wrapped_account
        )
        await asyncio.sleep(1)  # Give some time for the deletion to be processed
        await self.create_quotes(
            to_be_created=reconciled_orders.to_place,
            wrapped_account=wrapped_account,
        )

    async def execute_prologue(
        self, 
        calls: list[Calls],
        wrapped_account: WAccount
    ) -> None:
        self._logger.info(f"Executing prologue consisting of {len(calls)} calls")

        for call in calls:

            nonce = await wrapped_account.get_nonce()
            await wrapped_account.increment_nonce()

            sent = await wrapped_account.account.execute_v3(
                calls = call,
                auto_estimate=True,
                nonce = nonce
            )

            await wrapped_account.account.client.wait_for_tx(
                tx_hash=sent.transaction_hash,
                check_interval = 0.5
            )

            self._logger.info("Prologue call executed.")

    async def delete_quotes(
        self,
        wrapped_account: WAccount,
        to_be_canceled: list[BasicOrder],
    ) -> None:
        """Delete quotes based on the market maker's strategy."""
        self._logger.info(f"Deleting {len(to_be_canceled)} quotes")
        for order in to_be_canceled:
            nonce = await wrapped_account.get_nonce()
            await wrapped_account.increment_nonce()
            # TODO: Use ResourceBound instead of auto_estimate when invoking

            call = self.market.get_close_order_call(order=order)

            sent = await wrapped_account.account.execute_v3(
                calls=call,
                auto_estimate=True,
                nonce = nonce
            )

            await wrapped_account.account.client.wait_for_tx(
                tx_hash=sent.transaction_hash,
                check_interval = 0.5
            )


            metrics.track_orders_canceled(1)

            self._logger.info("Canceling: %s, nonce: %s", order.order_id, nonce)

        self._logger.info("Quotes deleted")

    async def create_quotes(
        self,
        wrapped_account: WAccount,
        to_be_created: list[FutureOrder],
    ) -> None:
        """Create quotes based on the market maker's strategy."""
        self._logger.info(f"Creating {len(to_be_created)} quotes")
        for order in to_be_created:

            nonce = await wrapped_account.get_nonce()
            await wrapped_account.increment_nonce()

            self._logger.info(
                "Soon to submit order: q: %s, p: %s, s: %s, nonce: %s",
                order.amount,
                order.price,
                order.order_side,
                nonce,
            )
            self._logger.debug(
                "Soon to submit order: %s",
                dict(
                    market_id=self.market.market_cfg.market_id,
                    order_price=order.price,
                    order_size=order.amount,
                    order_side=(order.order_side, None),
                    order_type=("Basic", None),
                    time_limit=("GTC", None),
                    nonce=nonce,
                ),
            )
            # TODO: Use ResourceBound instead of auto_estimate when invoking

            call = self.market.get_submit_order_call(order=order)

            sent = await wrapped_account.account.execute_v3(
                calls=call,
                auto_estimate=True,
                nonce = nonce
            )

            await wrapped_account.account.client.wait_for_tx(
                tx_hash=sent.transaction_hash,
                check_interval = 0.5
            )

            metrics.track_orders_sent(1)

            self._logger.info(
                "Submitting order: q: %s, p: %s, s: %s, nonce: %s",
                order.amount,
                order.price,
                order.order_side,
                nonce,
            )
        self._logger.info("Quotes created")
