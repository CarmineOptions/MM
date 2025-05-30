# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


# This bot serves as market making bot for Remus DEX and Ekubo DEX.

import logging

from marketmaking.enums import Urgency
from marketmaking.market import Market
from marketmaking.state import State
from marketmaking.waccount import WAccount
from marketmaking.pocmmmodel import POCMMModel
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
        accounts: list[WAccount],
        markets: list[Market],
        account_market_pairs: dict[WAccount, list[Market]],
        state: State,
        mm_model: POCMMModel, # FIXME: this should be a base class
        reconciler, # TODO: type
        claim_rule, # TODO: type
        transaction_builder: TransactionBuilder,
        blockchain_connectors, # TODO: type
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
        self._logger.info('Initializing MarketMaker')
        
        self.accounts: list[WAccount] = accounts
        self.map_accounts: dict[int, WAccount] = {account.address: account for account in accounts}
        self.markets: dict[int, Market] = {market.market_id: market for market in markets}
        # List of all markets for give account. {account: [market1, market2],...}
        self.account_market_pairs: dict[int, list[Market]] = {
            _account.address: _markets
            for _account, _markets in account_market_pairs.items()
        }
        # List of all accounts involved in a given market. {market: [account1, account2],...}
        self.market_account_pairs: dict[Market, list[WAccount]] = {}
        for market in self.markets.values():
            self.market_account_pairs[market] = []
            for account in self.accounts:
                if market in self.account_market_pairs[account.address]:
                    self.market_account_pairs[market].append(account)

        self.state = state
        self.mm_model = mm_model
        self.reconciler = reconciler
        self.claim_rule = claim_rule
        self.transaction_builder: TransactionBuilder = transaction_builder
        self.blockchain_connectors = blockchain_connectors # TODO: type

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



    async def pulse(self, data: dict) -> None:
        '''
        data are essentially all events coming from trading venues. Initially (in the first iteration)
        it is just price updates.

        :param data: New data to be added to the self.state.

        data = {
            'type': ...,
            'market_id': ...,
            'data': ...,        
        }
        '''

        # Update the state with new data.
        self.state.market_states[data['market_id']].update(data)

        # Updating only for the market that received update.
        if data['type'] == 'custom_oracle':

            # Claim in case we have some claimable assets.
            await self.claim_tokens(data['market_id'])

            # FIXME: parts here are used from the old version of market maker.
            # To do this properly, calculate teh optimal orders for the market (don't iterate over accounts).
            # Reconcile optimal vs. current orders (across accounts).
            # Build transactions and push them through the transaction builder.
            for account in self.market_account_pairs[self.markets[data['market_id']]]:
                # Calculate optimal orders for the market.
                to_be_canceled, to_be_created = self.mm_model.get_optimal_orders(
                    account,
                    self.state.market_states[data['market_id']]
                )
                self._logger.info('to_be_canceled: %s, to_be_created: %s', to_be_canceled, to_be_created)
                # assert False, "TODO: implement the rest of the logic"

                # Reconcile the orders for the market.
                # FIXME: reconciliation happened in the POCMMModel.

                # Push the orders from the transaction builder through the blockchain connector.
                await self.transaction_builder.build_transactions(
                    wrapped_account=account,
                    to_be_canceled=to_be_canceled,
                    to_be_created=to_be_created
                )



    async def claim_tokens(self, market_id: int) -> None:
        '''
        Initially it claims all the time. Later, it will claim only when needed.
        TODO: claim only when needed.
        :param market_id: Market ID for which to claim tokens.
        '''
        market = self.markets[market_id]
        accounts = self.market_account_pairs[market]

        for account in accounts:
            # Claim tokens for the market.
            for token_address in [market.base_token_address, market.quote_token_address]:
                claimable = await market.dex_contract.functions['get_claimable'].call(
                    token_address = token_address,
                    user_address = account.address
                )
                self._logger.info(
                    'Claimable amount is %s for token %s, account %s.',
                    claimable, hex(token_address), hex(account.address)
                )
                if claimable[0]:
                    self._logger.info(f'Claiming')
                    latest_nonce = await account.get_nonce()
                    max_fee = await self._get_max_fee(account, Urgency.MEDIUM)
                    # TODO: push this into the transaction builder.
                    # TODO: Use ResourceBound instead of auto_estimate when invoking
                    await market.dex_contract.functions['claim'].invoke_v3(
                        token_address = token_address,
                        amount = claimable[0],
                        nonce = latest_nonce,
                        auto_estimate=True
                    )
                    await account.increment_nonce()
                self._logger.info(
                    'Claim done for account %s, dex %s, market %s.',
                    hex(account.address), hex(int(market.dex_address, 16)), market_id
                )


    async def _setup_unlimited_approvals(self) -> None:
        """Set up unlimited approvals for base and quote tokens."""
        self._logger.info("Setting up unlimited approvals for tokens...")

        for account in self.accounts:
            nonce = await account.get_nonce()

            # TODO: Use ResourceBound instead of auto_estimate when invoking
            max_fee = await self._get_max_fee(account, Urgency.MEDIUM)

            for market in self.account_market_pairs[account.address]:
                # Approve base token

                await (await market.base_token_contract.functions['approve'].invoke_v3(
                    spender=int(market.dex_address, 16),
                    amount=MAX_UINT,
                    nonce=nonce,
                    auto_estimate=True
                )).wait_for_acceptance()
                nonce += 1
                self._logger.info(
                    'Set unlimited approval for address: %s, base token: %s',
                    hex(account.address),
                    hex(market.base_token_address)
                )

                # Approve quote token
                await (await market.quote_token_contract.functions['approve'].invoke_v3(
                    spender=int(market.dex_address, 16),
                    amount=MAX_UINT,
                    nonce=nonce,
                    auto_estimate=True
                )).wait_for_acceptance()
                nonce += 1
                self._logger.info(
                    'Set unlimited approval for address: %s, quote token: %s',
                    hex(account.address),
                    hex(market.quote_token_address)
                )
                self._logger.info(f"Set unlimited approval for address")

                await account.set_latest_nonce(nonce)
        self._logger.info(f"Setting unlimited approvals is done.")


    async def _get_max_fee(self, account: WAccount, urgency: Urgency) -> int:
        '''
        Finds optimal maximum fee for the transaction. For given urgency level.
        :param account: Account to be used for the transaction.
        :param urgency: Urgency level for the transaction.

        :return: Maximum fee for the transaction.

        FIME: Find different max fee for different accounts.
        FXME: This might be based on the current gas price. That's why this is async.
        '''
        if urgency == Urgency.LOW:
            return MAX_FEE
        elif urgency == Urgency.MEDIUM:
            return MAX_FEE
        elif urgency == Urgency.HIGH:
            return MAX_FEE
        else:
            raise ValueError(f"Invalid urgency level: {urgency}")


    # async def _get_nonce(self, account: WAccount) -> int:
    #     """
    #     Get the nonce for the given account.
    #     :param account: Account to be used for the transaction.
    #     :return: Nonce for the transaction.
    #     """
    #     return await account.get_nonce()
        

    def __str__(self) -> str:
        return f"""« MM market maker for market {self.markets}»"""

    def __repr__(self) -> str:
        return f"{self}"
