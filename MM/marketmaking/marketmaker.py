# # ⚠ Warning
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


# This bot serves as market making bot for Remus DEX and Ekubo DEX.


import logging
import traceback
import typing

from datetime import datetime
from decimal import Decimal

from ..observables import EventSource
from .orderreconciler import OrderReconciler
from .orderchain.chain import Chain

############################
# Event-driven market-maker.
############################


class MarketMaker:
    def __init__(
        self,
        accounts: TODO, # Starknet account classes
        markets: TODO, # [Remus, Ekubo]
        state: TODO, # Contains the current visible state of the market and it also includes the inflight orders (transactions). Orderbook, trades, my orders, my inflight orders, claimable assets.
        chain: TODO, # Contains all the logic for finding "optimal" orders in the market (where to quote and what to quote). Logic is based on Elements
        reconciler: TODO, # Compares visible and inflight orders against "optimal" orders and decides what to create and what to cancel.
        claim_rule: TODO, # Rules that drive claiming of assets.
        transaction_builder: TODO, # Creates transactions that are sent out to the blockchain
        blockchain_connectors: TODO, # Sends transactions out to the blockchain
    ) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        
        self.accounts: typing.List[TODO] = accounts
        self.markets: typing.List[TODO] = markets
        self.state: TODO = state
        self.chain: TODO = chain
        self.reconciler: TODO = reconciler
        self.claim_rule: TODO = claim_rule
        self.transaction_builder: TODO = transaction_builder
        self.blockchain_connectors: typing.List[TODO] = blockchain_connectors



    def pulse(self, data: TODO) -> None:
        '''
        :param data: New data to be added to the self.state.
        '''

    def __str__(self) -> str:
        return f"""« MM market maker for market {self.markets}»"""

    def __repr__(self) -> str:
        return f"{self}"