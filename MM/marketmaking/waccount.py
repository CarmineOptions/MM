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
        self._logger.info("Initializing WAccount: %s", hex(account.address))

        self.account = account
        self.address = account.address

        # There will be inflights transactions for this account.
        # This is used to find the latest nonce for this account.
        self._latest_transaction_timestamp: Optional[int] = None
        # The latest transaction nonce for this account. It might not be the actual latest nonce,
        # since the latest transaction might have failed.
        self._latest_transaction_nonce: Optional[int] = None

    async def get_nonce(self) -> int:
        """
        Get the on-chain nonce for the account and compare it with the latest
        self._latest_transaction_nonce.
        If the self._latest_transaction_timestamp is recent, use
        the self._latest_transaction_nonce. Otherwise use the on-chain nonce.

        :return: Nonce for the transaction.
        """
        if (self._latest_transaction_nonce is None) or (
            self._latest_transaction_timestamp is None
        ):
            on_chain_nonce = await self.account.get_nonce()
            self._logger.info(
                "On-chain nonce for account A %s: %s", hex(self.address), on_chain_nonce
            )
            return on_chain_nonce
        elif (
            datetime.datetime.now().timestamp() - self._latest_transaction_timestamp
        ) < self.PREFER_ONCHAIN_NONCE_THRESHOLD:
            # If the latest transaction was recent, use the latest nonce.
            self._logger.info(
                "Non-On-chain nonce for account B %s: %s",
                hex(self.address),
                self._latest_transaction_nonce,
            )
            return self._latest_transaction_nonce

        # If the latest transaction was not recent, use the on-chain nonce.
        on_chain_nonce = await self.account.get_nonce()
        self._logger.info(
            "On-chain nonce for account C %s: %s", hex(self.address), on_chain_nonce
        )
        return on_chain_nonce

    async def set_latest_nonce(self, nonce: int) -> None:
        """
        Set the latest nonce for the account.
        :param nonce: Nonce to be set.
        """
        self._logger.info(
            "Setting latest nonce to: %s, from %s",
            nonce,
            self._latest_transaction_nonce,
        )
        self._latest_transaction_nonce = nonce
        self._latest_transaction_timestamp = int(datetime.datetime.now().timestamp())

    async def increment_nonce(self) -> None:
        """
        Increment the latest nonce for the account.
        This is used to ensure that the next transaction will have a unique nonce.
        """
        latest_nonce = await self.get_nonce()
        await self.set_latest_nonce(latest_nonce + 1)


    async def reset_latest_nonce(self) -> None:
        """
        Reset the latest nonce for the account.
        This is usually used when there is observed error between the on chain nonce and the self._latest_transaction_nonce.
        """
        self._logger.info('Resetting latest nonce from %s', self._latest_transaction_nonce)
        self._latest_transaction_nonce = None
        self._latest_transaction_timestamp = None
