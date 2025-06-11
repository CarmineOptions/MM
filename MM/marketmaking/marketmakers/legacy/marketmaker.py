# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


# This bot serves as market making bot for Remus DEX and Ekubo DEX.

import logging

from marketmaking.market import Market
from marketmaking.waccount import WAccount
from state.state import State
from .pocmmmodel import POCMMModel
from marketmaking.transaction_builder import TransactionBuilder


############################
# Constants
############################
MAX_FEE = 101222419383266
MAX_UINT = 2**256 - 1


############################
# TODO stuff.
############################

# FIXME: pass logger everywhere

############################
# Event-driven market-maker.
############################


class MarketMaker:
    def __init__(
        self,
        account: WAccount,
        market: Market,
        mm_model: POCMMModel,  # FIXME: this should be a base class
        reconciler: None,  # TODO: type
        claim_rule: None,  # TODO: type
        transaction_builder: TransactionBuilder,
        blockchain_connectors: None,  # TODO: type
    ) -> None:
        """
        :param accounts: List of Starknet account classes.
        :param markets: List of Starknet DEXes (Remus, Ekubo).
        :param state: Contains the current visible state of the market and it also includes
            the inflight orders (transactions). Orderbook, trades, my orders, my inflight orders,
            claimable assets.
        :param mm_model: Contains all the logic for finding "optimal" orders in the market (where to
            quote and what to quote). Logic is based on Elements
        :param reconciler: Compares visible and inflight orders against "optimal" orders
            and decides what to create and what to cancel.
        :param claim_rule: Rules that drive claiming of assets.
        :param transaction_builder: Creates transactions that are sent out to the blockchain
        :param blockchain_connectors: Sends transactions out to the blockchain
        """
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._logger.info("Initializing MarketMaker")

        self.account = account
        self.market = market

        self.mm_model = mm_model
        self.reconciler = reconciler
        self.claim_rule = claim_rule
        self.transaction_builder: TransactionBuilder = transaction_builder
        self.blockchain_connectors = blockchain_connectors  # TODO: type

    async def initialize_trading(self) -> None:
        """
        Initialize the trading process.
        This method should be called to start the market-making process.

        It:
        - Sets unlimited approve to given self.markets for given self.accounts.
        """
        self._logger.info("Initializing trading...")
        await self._setup_unlimited_approvals()

        # During the first iteration we don't need orderbook(s).
        # for market in self.markets:
        #     await self.state.market_states[market].orderbook.update()

    async def pulse(self, state: State) -> None:
        """
        Main pulsing function that takes in updated State and then 
        proceeds to claim tokens, calculate optimal orders and send them
        to the market.
        """

        # Claim in case we have some claimable assets.
        await self.claim_tokens()

        # FIXME: parts here are used from the old version of market maker.
        # To do this properly, calculate teh optimal orders for the market (don't iterate over accounts).
        # Reconcile optimal vs. current orders (across accounts).
        # Build transactions and push them through the transaction builder.

        # Calculate optimal orders for the market.
        to_be_canceled, to_be_created = self.mm_model.get_optimal_orders(
            self.account, state
        )
        self._logger.info(
            "to_be_canceled: %s, to_be_created: %s",
            to_be_canceled,
            to_be_created,
        )

        # Reconcile the orders for the market.
        # FIXME: reconciliation happened in the POCMMModel.

        # Push the orders from the transaction builder through the blockchain connector.
        await self.transaction_builder.build_transactions(
            wrapped_account=self.account,
            to_be_canceled=to_be_canceled,
            to_be_created=to_be_created,
        )

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

    async def _setup_unlimited_approvals(self) -> None:
        """Set up unlimited approvals for base and quote tokens."""
        self._logger.info("Setting up unlimited approvals for tokens...")

        # TODO: Use ResourceBound instead of auto_estimate when invoking
        account = self.account
        market = self.market

        nonce = await account.get_nonce()

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

    def __str__(self) -> str:
        return f"""« MM market maker for market {self.market}»"""

    def __repr__(self) -> str:
        return f"{self}"
