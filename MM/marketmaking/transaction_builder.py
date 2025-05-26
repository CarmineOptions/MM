
from typing import Any, Dict
import logging

from marketmaking.waccount import WAccount

class TransactionBuilder:

    '''Class to build transactions for the market maker.
    This class is responsible for creating and managing transactions
    that will be sent to the blockchain for execution.
    It handles the logic for updating and deleting quotes, as well as
    submitting new orders based on the market maker's strategy.
    '''

    def __init__(self, dex_contract, market_id: int, market_cfg: Dict[str, Any], max_fee: int) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._logger.info('Initializing TransactionBuilder')

        # FIXME: This will have to be replaced with multiple contracts(DEXes).
        self.dex_contract = dex_contract
        self.market_id = market_id
        self.market_cfg = market_cfg

        self.max_fee = max_fee
        

    async def build_transactions(self, wrapped_account:WAccount, to_be_canceled, to_be_created):
        self._logger.info('Deleting quotes')
        await self.delete_quotes(
            wrapped_account=wrapped_account,
            dex_contract=self.dex_contract,
            to_be_canceled=to_be_canceled,
            max_fee=self.max_fee
        )
        self._logger.info('Done with deleting quotes')
        self._logger.info('Creating quotes')
        await self.create_quotes(
            wrapped_account,
            market_id=self.market_id,
            market_cfg=self.market_cfg,
            dex_contract=self.dex_contract,
            to_be_created=to_be_created,
            max_fee=self.max_fee
        )
        self._logger.info('Done with creating quotes')
        

    async def delete_quotes(
        self,
        wrapped_account: WAccount,
        dex_contract,
        to_be_canceled,
        max_fee
    ) -> None:
        '''Delete quotes based on the market maker's strategy.'''
        self._logger.info('Deleting quotes')
        for order in to_be_canceled:
            nonce = await wrapped_account.get_nonce()
            await dex_contract.functions['delete_maker_order'].invoke_v1(
                maker_order_id=order['maker_order_id'],
                max_fee=max_fee,
                nonce=nonce
            )
            logging.info(f"Canceling: {order['maker_order_id']}")
            await wrapped_account.increment_nonce()


    async def create_quotes(
        self,
        wrapped_account: WAccount,
        market_id,
        market_cfg,
        dex_contract,
        to_be_created,
        max_fee
    ) -> None:
        '''Create quotes based on the market maker's strategy.'''
        
        for order in to_be_created:
            if order['order_side'] == 'ask':
                target_token_address = market_cfg[1]['base_token']
                order_side = 'Ask'
            else:
                target_token_address = market_cfg[1]['quote_token']
                order_side = 'Bid'

            nonce = await wrapped_account.get_nonce()

            self._logger.info("Soon to sumbit order: q: %s, p: %s, s: %s, nonce: %s", order['amount'], order['price'], order_side, nonce)
            self._logger.debug("Soon to sumbit order: %s", dict(
                market_id = market_id,
                target_token_address = target_token_address,
                order_price = order['price'],
                order_size = order['amount'],
                order_side = (order_side, None),
                order_type = ('Basic', None),
                time_limit = ('GTC', None),
                max_fee = max_fee,
                nonce = nonce
            ))
            await dex_contract.functions['submit_maker_order'].invoke_v1(
                market_id = market_id,
                target_token_address = target_token_address,
                order_price = order['price'],
                order_size = order['amount'],
                order_side = (order_side, None),
                order_type = ('Basic', None),
                time_limit = ('GTC', None),
                max_fee = max_fee,
                nonce = nonce
            )
            await wrapped_account.increment_nonce()
            self._logger.info("Submitting order: q: %s, p: %s, s: %s, nonce: %s", order['amount'], order['price'], order_side, nonce)
        self._logger.info('Done with order changes')
