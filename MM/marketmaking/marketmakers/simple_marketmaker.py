
import logging

from marketmaking.market import Market
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
        await self._setup_unlimited_approvals()

    async def _setup_unlimited_approvals(self) -> None:
        """Set up unlimited approvals for base and quote tokens."""
        self._logger.info("Setting up unlimited approvals for tokens...")

        # TODO: Use ResourceBound instead of auto_estimate when invoking
        account = self.account
        market = self.market

        nonce = await account.get_nonce()

        # NOTE: Currently remus-specific, will change once ekubo and other venues are added

        # Approve base token
        await (
            await market.base_token_contract.functions["approve"].invoke_v3(
                spender=int(market.remus_client.address, 16),
                amount=MAX_UINT,
                nonce=nonce,
                auto_estimate=True,
            )
        ).wait_for_acceptance()
        nonce += 1
        self._logger.info(
            "Set unlimited approval for address: %s, base token: %s",
            hex(account.address),
            hex(market.market_cfg.base_token.address),
        )

        # Approve quote token
        await (
            await market.quote_token_contract.functions["approve"].invoke_v3(
                spender=int(market.remus_client.address, 16),
                amount=MAX_UINT,
                nonce=nonce,
                auto_estimate=True,
            )
        ).wait_for_acceptance()
        nonce += 1
        self._logger.info(
            "Set unlimited approval for address: %s, quote token: %s",
            hex(account.address),
            hex(market.market_cfg.quote_token.address),
        )
        self._logger.info("Set unlimited approval for address")

        await account.set_latest_nonce(nonce)
        self._logger.info("Setting unlimited approvals is done.")

    async def claim_tokens(self) -> None:
        """
        Initially it claims all the time. Later, it will claim only when needed.
        TODO: claim only when needed.
        :param market_id: Market ID for which to claim tokens.
        """
        market = self.market
        account = self.account
        # Claim tokens for the market.

        logging.info("Claiming tokens for market_id: %s", self.market.market_id)
        
        for token in [market.market_cfg.base_token, market.market_cfg.quote_token]:
            claimable = await market.remus_client.view.get_claimable(
                token=token, user_address=account.address
            )

            self._logger.info(
                "Claimable amount is %s for token %s, account %s.",
                claimable,
                hex(token.address),
                hex(account.address),
            )

            if claimable:
                self._logger.info("Claiming")
                latest_nonce = await account.get_nonce()
                # TODO: push this into the transaction builder.
                # TODO: Use ResourceBound instead of auto_estimate when invoking

                call = market.remus_client.prep_claim_call(
                    token=token,
                    amount=claimable,
                )

                await call.invoke(auto_estimate=True, nonce=latest_nonce)

                await account.increment_nonce()

            self._logger.info(
                "Claim done for account %s, dex %s, market %s.",
                hex(account.address),
                hex(int(market.remus_client.address, 16)),
                self.market.market_id,
            )

    async def pulse(self, state: State) -> None:

        desired_orders = self.order_chain.process(state)

        open_orders = state.account.open_orders

        reconciled = self.order_reconciler.reconcile(
            existing_orders=open_orders, 
            state = state,
            desired_orders=desired_orders
        )

        await self.tx_builder.build_transactions(
            wrapped_account=self.account,
            to_be_canceled=reconciled.to_cancel,
            to_be_created=reconciled.to_place
        )
