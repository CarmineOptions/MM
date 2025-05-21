from typing import Optional
import datetime
import logging

from starknet_py.net.account.account import Account



class WAccount:

    PREFER_ONCHAIN_NONCE_THRESHOLD = 60

    """
    This is a wrapper class for the Starknet account.
    """
    def __init__(self, account: Account) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._logger.info('Initializing WAccount: %s', hex(account.address))

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
        elif (datetime.datetime.now().timestamp() - self._latest_transaction_timestamp) < self.PREFER_ONCHAIN_NONCE_THRESHOLD:
            # If the latest transaction was recent, use the latest nonce.
            return self._latest_transaction_nonce

        # If the latest transaction was not recent, use the on-chain nonce.
        return on_chain_nonce


    async def set_latest_nonce(self, nonce: int) -> None:
        """
        Set the latest nonce for the account.
        :param nonce: Nonce to be set.
        """
        self._logger.info('Setting latest nonce to: %s, from %s', nonce, self._latest_transaction_nonce)
        self._latest_transaction_nonce = nonce
        self._latest_transaction_timestamp = datetime.datetime.now().timestamp()
