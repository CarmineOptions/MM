


import logging
from typing import final

from typing import Iterable
from starknet_py.net.client_models import Calls, Call

from platforms.starknet.starknet_account import WAccount
from marketmaking.reconciling.order_reconciler import ReconciledOrders
from markets.market import Market
from monitoring import metrics
from .tx_builder import TxBuilder


@final
class BundlingTransactionBuilder(TxBuilder):
    '''
    BundlingTransactionBuilder is a transaction builder that bundles multiple
    transactions into a single transaction. It is used to cancel and place orders
    in a single transaction to reduce the number of transactions sent to the network.

    Note that currently it bundles all cancel and place orders together without
    accounting for the steps the big transaction will take.
    '''
    def __init__(
        self,
        market: Market,
    ) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._logger.info("Initializing TransactionBuilder")

        self.market = market


    async def build_and_execute_transactions(
        self,
        wrapped_account: WAccount,
        reconciled_orders: ReconciledOrders,
        prologue: list[Calls],
    ) -> None:
        '''
        Build and execute one big transaction that cancels and places all 
        the reconciled orders.
        '''
        n_cancels = len(reconciled_orders.to_cancel)
        n_places = len(reconciled_orders.to_place)
        n_prologues = len(prologue)

        self._logger.info(
            f"Canceling {n_cancels} orders, "
            f"placing {n_places} orders, "
            f"executing {n_prologues} prologues."
        )
        self._logger.info(f"Canceling orders: {reconciled_orders.to_cancel}")
        self._logger.info(f"Placing orders: {reconciled_orders.to_place}")
        
        # Prepare the calls
        cancel_calls = [
            self.market.get_close_order_call(o) 
            for o in reconciled_orders.to_cancel
        ]

        place_calls = [
            self.market.get_submit_order_call(o) 
            for o in reconciled_orders.to_place
        ]

        single_cancel_call = _get_single_call_list(cancel_calls)
        single_place_call = _get_single_call_list(place_calls)

        bundled_call = single_cancel_call + single_place_call
        
        # Bundle the call with prologue
        complete_tx = _get_single_call_list(prologue) + bundled_call

        # Execute the tx
        nonce = await wrapped_account.get_nonce()

        self._logger.info("Executing bundled transaction.")
        sent = await wrapped_account.account.execute_v3(
            calls=complete_tx,
            auto_estimate=True,
            nonce = nonce
        )
        self._logger.info(f"Bundled transaction `{hex(sent.transaction_hash)}` sent.")

        await wrapped_account.increment_nonce()
        await wrapped_account.account.client.wait_for_tx(
            tx_hash=sent.transaction_hash,
            check_interval = 0.5
        )

        self._logger.info(f"Executed transaction {hex(sent.transaction_hash)} successfully")

        metrics.track_orders_canceled(n_cancels)
        metrics.track_orders_sent(n_places)


def _get_single_call_list(calls: Calls | list[Calls]) -> list[Call]:
    if isinstance(calls, Call):
        return [calls]
    
    single_call_list: list[Call] = []

    for call in calls:
        if isinstance(call, Call):
            single_call_list.append(call)
        if isinstance(call, Iterable):
            single_call_list.extend(call)

    return single_call_list
    