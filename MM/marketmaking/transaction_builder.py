import asyncio
import logging

from markets.market import Market
from venues.remus.remus import RemusDexClient
from venues.remus.remus_market_configs import RemusMarketConfig
from marketmaking.order import BasicOrder, FutureOrder
from marketmaking.waccount import WAccount
from monitoring import metrics


class TransactionBuilder:
    """Class to build transactions for the market maker.
    This class is responsible for creating and managing transactions
    that will be sent to the blockchain for execution.
    It handles the logic for updating and deleting quotes, as well as
    submitting new orders based on the market maker's strategy.
    """

    def __init__(
        self,
        market: Market,
        max_fee: int,
    ) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._logger.info("Initializing TransactionBuilder")

        # FIXME: This will have to be replaced with multiple contracts(DEXes).
        self.market = market

        self.max_fee = max_fee

    async def build_transactions(
        self,
        wrapped_account: WAccount,
        to_be_canceled: list[BasicOrder],
        to_be_created: list[FutureOrder],
    ) -> None:
        await self.delete_quotes(
            to_be_canceled=to_be_canceled,
            wrapped_account=wrapped_account
        )
        await asyncio.sleep(1)  # Give some time for the deletion to be processed
        await self.create_quotes(
            to_be_created=to_be_created,
            wrapped_account=wrapped_account,
        )

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
                tx_hash=sent.transaction_hash
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
                "Soon to sumbit order: q: %s, p: %s, s: %s, nonce: %s",
                order.amount,
                order.price,
                order.order_side,
                nonce,
            )
            self._logger.debug(
                "Soon to sumbit order: %s",
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
                tx_hash=sent.transaction_hash
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
