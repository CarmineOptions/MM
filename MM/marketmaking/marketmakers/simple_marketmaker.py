import logging

from markets.market import Market
from marketmaking.orderchain.order_chain import OrderChain
from marketmaking.reconciling.order_reconciler import OrderReconciler
from marketmaking.transaction_builder import TransactionBuilder
from marketmaking.waccount import WAccount
from state.state import State

MAX_UINT = 2**256 - 1


class SimpleMarketMaker:
    """
    Simple MarketMaker that makes market on single pair using single account.
    """

    def __init__(
        self,
        account: WAccount,
        market: Market,
        order_reconciler: OrderReconciler,
        order_chain: OrderChain,
        tx_builder: TransactionBuilder,
    ):
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._logger.info("Initializing MarketMaker")

        self.account = account
        self.market = market
        self.order_reconciler = order_reconciler
        self.order_chain = order_chain
        self.tx_builder = tx_builder

    async def initialize_trading(self) -> None:
        """
        Initialize the trading process.
        This method should be called to start the market-making process.

        It:
        - Sets unlimited approve to given self.markets for given self.accounts.
        """
        self._logger.info("Initializing trading...")
        await self.market.setup(self.account)

    async def claim_tokens(self, state: State) -> None:
        """
        Initially it claims all the time. Later, it will claim only when needed.
        TODO: claim only when needed.
        :param market_id: Market ID for which to claim tokens.
        """
        market = self.market
        account = self.account
        # Claim tokens for the market.

        logging.info("Claiming tokens for market_id: %s", self.market.market_cfg.market_id)

        for claimable_token in [state.account.position.withdrawable_base, state.account.position.withdrawable_quote]:
            self._logger.info(
                "Claimable amount is %s for token %s, account %s.",
                claimable_token.amount_hr,
                hex(claimable_token.instrument.address),
                hex(account.address),
            )

            if claimable_token.amount_raw:
                self._logger.info("Claiming")
                latest_nonce = await account.get_nonce()
                # TODO: push this into the transaction builder.
                # TODO: Use ResourceBound instead of auto_estimate when invoking


                call = market.get_withdraw_call(state=state, amount=claimable_token)

                sent = await self.account.account.execute_v3(
                    calls = call,
                    auto_estimate=True,
                    nonce = latest_nonce
                )

                await self.account.account.client.wait_for_tx(
                    tx_hash = sent.transaction_hash,
                    check_interval = 0.5
                )


                await account.increment_nonce()

            self._logger.info(
                "Claim done for account %s, market %s.",
                hex(account.address),
                self.market.market_cfg.market_id,
            )

    async def pulse(self, state: State) -> None:

        await self.claim_tokens(state=state)
        
        desired_orders = self.order_chain.process(state)

        open_orders = state.account.orders.active

        reconciled = self.order_reconciler.reconcile(
            existing_orders=open_orders, state=state, desired_orders=desired_orders
        )

        await self.tx_builder.build_transactions(
            wrapped_account=self.account,
            to_be_canceled=reconciled.to_cancel,
            to_be_created=reconciled.to_place,
        )
