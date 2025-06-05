import asyncio
import logging

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
        remus_client: RemusDexClient,
        market_id: int,
        market_cfg: RemusMarketConfig,
        max_fee: int,
    ) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._logger.info("Initializing TransactionBuilder")

        # FIXME: This will have to be replaced with multiple contracts(DEXes).
        self.remus_client = remus_client
        self.market_id = market_id
        self.market_cfg = market_cfg

        self.max_fee = max_fee

    async def build_transactions(
        self,
        wrapped_account: WAccount,
        to_be_canceled: list[BasicOrder],
        to_be_created: list[FutureOrder],
    ) -> None:
        self._logger.info("Deleting quotes")
        await self.delete_quotes(
            wrapped_account=wrapped_account,
            remus_client=self.remus_client,
            to_be_canceled=to_be_canceled,
        )
        self._logger.info("Done with deleting quotes")
        self._logger.info("Creating quotes")
        await asyncio.sleep(1)  # Give some time for the deletion to be processed
        await self.create_quotes(
            wrapped_account,
            market_cfg=self.market_cfg,
            remus_client=self.remus_client,
            to_be_created=to_be_created,
        )
        self._logger.info("Done with creating quotes")

    async def delete_quotes(
        self,
        wrapped_account: WAccount,
        remus_client: RemusDexClient,
        to_be_canceled: list[BasicOrder],
    ) -> None:
        """Delete quotes based on the market maker's strategy."""
        self._logger.info("Deleting quotes F")
        for order in to_be_canceled:
            nonce = await wrapped_account.get_nonce()
            await wrapped_account.increment_nonce()
            # TODO: Use ResourceBound instead of auto_estimate when invoking

            call = remus_client.prep_delete_maker_order_call(order=order)

            await (
                await call.invoke(auto_estimate=True, nonce=nonce)
            ).wait_for_acceptance()

            metrics.track_orders_canceled(1)

            self._logger.info("Canceling: %s, nonce: %s", order.order_id, nonce)

    async def create_quotes(
        self,
        wrapped_account: WAccount,
        market_cfg: RemusMarketConfig,
        remus_client: RemusDexClient,
        to_be_created: list[FutureOrder],
    ) -> None:
        """Create quotes based on the market maker's strategy."""

        for order in to_be_created:
            if order.order_side.lower() == "ask":
                target_token_address = market_cfg.base_token.address
                order_side = "Ask"
            else:
                target_token_address = market_cfg.quote_token.address
                order_side = "Bid"

            nonce = await wrapped_account.get_nonce()
            await wrapped_account.increment_nonce()

            self._logger.info(
                "Soon to sumbit order: q: %s, p: %s, s: %s, nonce: %s",
                order.amount,
                order.price,
                order_side,
                nonce,
            )
            self._logger.debug(
                "Soon to sumbit order: %s",
                dict(
                    market_id=market_cfg.market_id,
                    target_token_address=target_token_address,
                    order_price=order.price,
                    order_size=order.amount,
                    order_side=(order_side, None),
                    order_type=("Basic", None),
                    time_limit=("GTC", None),
                    nonce=nonce,
                ),
            )
            # TODO: Use ResourceBound instead of auto_estimate when invoking

            await (
                await remus_client.prep_submit_maker_order_call(
                    order=order,
                    market_cfg=market_cfg,
                ).invoke(auto_estimate=True, nonce=nonce)
            ).wait_for_acceptance()

            metrics.track_orders_sent(1)

            self._logger.info(
                "Submitting order: q: %s, p: %s, s: %s, nonce: %s",
                order.amount,
                order.price,
                order_side,
                nonce,
            )
        self._logger.info("Done with order changes")
