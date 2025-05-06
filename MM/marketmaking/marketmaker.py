# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


# This bot serves as market making bot for Remus DEX and Ekubo DEX.

from typing import List, Dict, Optional
import datetime
import enum
import logging
import traceback

from decimal import Decimal

from starknet_py.net.account.account import Account




############################
# Constants
############################
MAX_FEE = 101222419383266
MAX_UINT = 2**256 - 1


############################
# TODO stuff.
############################


class TODO:
    """TODO: Placeholder for the actual class definition.
    This should be replaced with the actual class that is being used in the code.
    """
    pass


class Market:
    """
    Describes the market and it's parameters.

    Has the all of the contracts needed to interact with the market.
    """

    def __init__(
            self,
            market_id: str,
            dex_contract: TODO,
            base_token_contract: TODO,
            quote_token_contract: TODO,
            dex_address: str,
            base_token_address: str,
            quote_token_address: str,
    ) -> None:
        self.market_id = market_id

        self.dex_contract = dex_contract
        self.base_token_contract = base_token_contract
        self.quote_token_contract = quote_token_contract

        self.dex_address = dex_address
        self.base_token_address = base_token_address
        self.quote_token_address = quote_token_address
    
    def restart_contracts(self) -> None:
        """
        Restart the contracts for the market.
        This method should be called to restart the contracts for the market.
        """
        # FIXME
        pass


class WAccount:

    PREFER_ONCHAIN_NONCE_THRESHOLD = 60

    """
    TODO
    This is a wrapper class for the Starknet account.
    """
    def __init__(self, account: Account) -> None:
        self.account = account
        self.address = account.address

        # There will be inflights transactions for this account.
        # This is used to find the latest nonce for this account.
        self._latest_transaction_timestamp: Optional[int] = None
        # The latest transaction nonce for this account. It might not be the actual latest nonce,
        # since the latest transaction might have failed.
        self._latest_transaction_nonce: Optional[int] = None


    async def get_nonce(self) -> int:
        '''
        Get the on-chain nonce for the account and compare it with the latest
        self._latest_transaction_nonce.
        If the self._latest_transaction_timestamp is recent, use 
        the self._latest_transaction_nonce. Otherwise use the on-chain nonce.

        :return: Nonce for the transaction.
        '''
        on_chain_nonce = await self.account.get_nonce()
        if self._latest_transaction_nonce is None:
            return on_chain_nonce
        elif self._latest_transaction_timestamp is None:
            return on_chain_nonce
        elif (datetime.datetime.now().timestamp() - self._latest_transaction_timestamp) < SELF.PREFER_ONCHAIN_NONCE_THRESHOLD:
            # If the latest transaction was recent, use the latest nonce.
            return self._latest_transaction_nonce

        # If the latest transaction was not recent, use the on-chain nonce.
        return on_chain_nonce


    async def set_latest_nonce(self, nonce: int) -> None:
        """
        Set the latest nonce for the account.
        :param nonce: Nonce to be set.
        """
        self._latest_transaction_nonce = nonce
        self._latest_transaction_timestamp = datetime.datetime.now().timestamp()

    


class Urgency(enum.Enum):
    """Urgency levels for transactions."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class Order:
    pass

class State:

    def __init__(self, markets: List[Market], accounts: List[WAccount]) -> None:
        self.market_states: Dict[str, StateMarket] = {
            market.market_id: StateMarket(accounts, market)
            for market in markets
        }

# FIXME: pass logger everywhere

class StateMarket:

    def __init__(self, accounts: List[WAccount], market: Market) -> None:
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


class POCMMModel:
    # POCMMModel contains the logic from the POC market maker. The goal is to test the SW and build the model later. 
    # The POCMMModel also contains reconciliation.
    def __init__(self, state_market: StateMarket) -> None:
        self.state_market: StateMarket = state_market
        pass

    def get_optimal_orders(self) -> List[Order]:
        return self._get_optimal_quotes(
            bids=self.state_market.my_orders['bid'],
            asks=self.state_market.my_orders['ask'],
            market_maker_cfg={
                'target_relative_distance_from_FP': 0.001, # where best order is created 
                'max_relative_distance_from_FP': 0.003, # too far from FP to be considered best (it is considered deep)
                'min_relative_distance_from_FP': 0.0005, # too close to FP to exist -> if closer kill the order

                'order_dollar_size': 200 * 10**18,  # in $
                'minimal_remaining_quote_size': 100,  # in $
                'max_number_of_orders_per_side': 3
            },
            market_cfg=,# FIXME
            fair_price=self.state_market.oracle['price']
        )


    def _get_optimal_quotes(asks, bids, market_maker_cfg, market_cfg, fair_price):
        """
        If an existing quote has lower than market_maker_cfg['minimal_remaining_quote_size'] quantity, it is requoted.
        
        Optimal quote is in market_maker_cfg['target_relative_distance_from_FP'] distance from the FP, where FP is binance price.
        The order is never perfect and market_maker_cfg['max_distance_from_FP'] from optimal quote price level is allowed, meaning
        that an old best quote is considered deep quote and new best is created if the distance is outside of what is ok.

        If the Best quote gets too close to FP, less than market_maker_cfg['min_distance_from_FP'] distance, it is canceled.
        """
        to_be_canceled = []
        to_be_created = []

        base_decimals = token_config.decimals[market_cfg[1]['base_token']]  # for example ETH
        quote_decimals = token_config.decimals[market_cfg[1]['quote_token']]  # for example USDC
        
        for side, side_name in [(asks, 'ask'), (bids, 'bid')]:
            to_be_canceled_side = []
            to_be_created_side = []
        
            for order in side:
                # If the remaining order size is too small requote (cancel order)
                if order['amount_remaining'] / 10**base_decimals * order['price'] / 10**base_decimals < market_maker_cfg['minimal_remaining_quote_size']:
                    logging.info(f"Canceling order because of insufficient amount. amount: {order['amount_remaining']}")
                    logging.debug(f"Canceling order because of insufficient amount. order: {order}")
                    to_be_canceled_side.append(order)
                    continue
                if (
                    (
                        (side_name == 'bid')
                        and
                        ((1 - market_maker_cfg['min_relative_distance_from_FP']) * fair_price < order['price'] / 10**base_decimals)
                    )
                    or
                    (
                        (side_name == 'ask')
                        and
                        (order['price'] / 10**base_decimals < (1 + market_maker_cfg['min_relative_distance_from_FP']) * fair_price)
                    )
                ):
                    logging.info(f"Canceling order because too close to FP. fair_price: {fair_price}, order price: {order['price'] / 10**base_decimals}")
                    logging.debug(f"Canceling order because too close to FP. order: {order}")
                    to_be_canceled_side.append(order)
            # If there is too many orders in the market that are not being canceled, cancel those with the most distant price from FP
            # to a point that only the "allowed" number of orders is being kept.
            if len(side) - len(to_be_canceled_side) > market_maker_cfg['max_number_of_orders_per_side']:
                # assumes "side" (e.g. asks and bids) are ordered from the best to the deepest
                to_be_canceled_side.extend(
                    [order for order in side if order not in to_be_canceled_side][market_maker_cfg['max_number_of_orders_per_side']:]
                )
            to_be_canceled.extend(to_be_canceled_side)
        
            # Create best order if there is no best order
            remaining = [order for order in side if order not in to_be_canceled]
            ordered_remaining = sorted(remaining, key=lambda x: x['price'] if side_name=='ask' else -x['price'])
            if (
                (not ordered_remaining)
                or
                (
                    (side_name == 'bid')
                    and
                    (order['price'] / 10**base_decimals < (1 - market_maker_cfg['max_relative_distance_from_FP']) * fair_price)
                )
                or
                (
                    (side_name == 'ask')
                    and
                    ((1 + market_maker_cfg['max_relative_distance_from_FP']) * fair_price < order['price'] / 10**base_decimals)
                )
            ):
                tick_size = market_cfg[1]['tick_size']
                base_decimals_ = 18 if market_cfg[0] == 3 else base_decimals
                if side_name == 'ask':
                    optimal_price = int(fair_price * (1 + market_maker_cfg['target_relative_distance_from_FP']) * 10**base_decimals_)
                    optimal_price = optimal_price // tick_size
                    optimal_price = optimal_price * tick_size + tick_size
                else:
                    optimal_price = int(fair_price * (1 - market_maker_cfg['target_relative_distance_from_FP']) * 10**base_decimals_)
                    optimal_price = optimal_price // tick_size
                    optimal_price = optimal_price * tick_size
                optimal_amount = market_maker_cfg['order_dollar_size'] / (optimal_price / 10**base_decimals_)
                optimal_amount = optimal_amount // market_cfg[1]['lot_size']
                optimal_amount = optimal_amount * market_cfg[1]['lot_size']
        
                order = {
                    'order_side': side_name,
                    'amount': int(optimal_amount),
                    'price': optimal_price
                }
                to_be_created.append(order)
        logging.info(f"Optimal quotes calculated: to_be_canceled: {len(to_be_canceled)}, to_be_created: {len(to_be_created)}")
        logging.debug(f"Optimal quotes calculated: to_be_canceled: {to_be_canceled}, to_be_created: {to_be_created}")
        return to_be_canceled, to_be_created


############################
# Event-driven market-maker.
############################

class MarketMaker:
    def __init__(
        self,
        accounts: List[WAccount],
        markets: List[Market],
        account_market_pairs: Dict[WAccount, List[Market]],
        state: TODO,
        mm_model: TODO,
        reconciler: TODO,
        claim_rule: TODO,
        transaction_builder: TODO,
        blockchain_connectors: TODO,
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
        handler = logging.FileHandler('marketmaker.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)
        
        self.accounts: List[WAccount] = accounts
        self.map_accounts: Dict[str, WAccount] = {account.address: account for account in accounts}
        self.markets: Dict[str, Market] = {market.market_id: market for market in markets}
        # List of all markets for give account. {account: [market1, market2],...}
        self.account_market_pairs: Dict[str, List[TODO]] = {_account.address: _markets for _account, _markets in account_market_pairs.items()}
        # List of all accounts involved in a given market. {market: [account1, account2],...}
        self.market_account_pairs: Dict[TODO, List[str]] = {}
        for market in self.markets.values():
            self.market_account_pairs[market] = []
            for account in self.accounts:
                if market in self.account_market_pairs[account]:
                    self.market_account_pairs[account].append(market)

        self.state: TODO = state
        self.mm_model: TODO = mm_model
        self.reconciler: TODO = reconciler
        self.claim_rule: TODO = claim_rule
        self.transaction_builder: TODO = transaction_builder
        self.blockchain_connectors: List[TODO] = blockchain_connectors

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



    def pulse(self, data: TODO) -> None:
        '''
        data are essentially all events coming from trading venues. Initially (in the first iteration)
        it is just price updates.

        :param data: New data to be added to the self.state.

        data = {
            'type': ...,
            'market': ...,
            'data': ...,        
        }
        '''

        # Update the state with new data.
        self.state.market_states[data['market_id']].update(data)

        # Updating only for the market that received update.

        # Claim in case we have some claimable assets.
        self.claim_tokens(data['market_id'])

        # Calculate optimal orders for the market.
        # FIXME: assumes only one account
        to_be_canceled, to_be_created = self.mm_model.get_optimal_orders(self.state.market_states[data['market_id']])

        # Reconcile the orders for the market.
        # FIXME: reconciliation happened in the POCMMModel.

        # Push the orders from the transaction builder through the blockchain connector.



    async def claim_tokens(self, market_id: str) -> None:
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
                claimable = await account.account.functions['get_claimable'].call(
                    token_address = token_address,
                    user_address = account.address
                )
                logging.info(
                    'Claimable amount is %s for token %s, account %s.',
                    claimable, hex(token_address), hex(account.address)
                )
                if claimable[0]:
                    logging.info(f'Claiming')
                    latest_nonce = await self._get_nonce(account)
                    max_fee = await self._get_max_fee(account, Urgency.MEDIUM)
                    # TODO: push this into the transaction builder.
                    await market.dex_contract.functions['claim'].invoke_v1(
                        token_address = token_address,
                        amount = claimable[0],
                        max_fee = max_fee,
                        nonce = latest_nonce
                    )
                logging.info(
                    'Claim done for account %s, dex %s, market %s.',
                    hex(account.address), hex(market.dex_address), market_id
                )


    async def _setup_unlimited_approvals(self) -> None:
        """Set up unlimited approvals for base and quote tokens."""
        self._logger.info("Setting up unlimited approvals for tokens...")

        for account in self.accounts:
            nonce = await self._get_nonce(account)

            max_fee = await self._get_max_fee(account, Urgency.MEDIUM)

            for market in self.account_market_pairs[account.address]:
                # Approve base token
                await (await market.base_token_contract.functions['approve'].invoke_v1(
                    spender=int(market.dex_address, 16),
                    amount=MAX_UINT,
                    max_fee=max_fee,
                    nonce=nonce
                )).wait_for_acceptance()
                nonce += 1
                self._logger.info(f"Set unlimited approval for address: {hex(account.address)}, base token: {hex(market.base_token_address)}")
        
                # Approve quote token
                await (await market.quote_token_contract.functions['approve'].invoke_v1(
                    spender=int(market.dex_address, 16),
                    amount=MAX_UINT,
                    max_fee=max_fee,
                    nonce=nonce
                )).wait_for_acceptance()
                nonce += 1
                self._logger.info(f"Set unlimited approval for address: {hex(account.address)}, quote token: {hex(market.quote_token_address)}")

                account.set_latest_nonce(nonce)
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


    async def _get_nonce(self, account: WAccount) -> int:
        """
        Get the nonce for the given account.
        :param account: Account to be used for the transaction.
        :return: Nonce for the transaction.
        """
        return await account.get_nonce()
        

    def __str__(self) -> str:
        return f"""« MM market maker for market {self.markets}»"""

    def __repr__(self) -> str:
        return f"{self}"