from dataclasses import dataclass
from decimal import Decimal
import logging
from typing import OrderedDict

from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.contract import Contract, PreparedFunctionInvokeV3


from MM.venues.remus.remus_market_configs import RemusMarketConfig, get_preloaded_remus_market_config
from instruments.instrument import InstrumentAmount
from marketmaking.order import BasicOrder, FutureOrder
from instruments.starknet import StarknetToken, get_sn_token_from_address

REMUS_ADDRESS = '0x067e7555f9ff00f5c4e9b353ad1f400e2274964ea0942483fae97363fd5d7958'
REMUS_IDENTIFIER = 'REMUS'


class RemusDexView:
    """
    Class representing RemusDex view functions for polling the dex state.
    """
    def __init__(self, contract: Contract):
        self._contract = contract

    @staticmethod
    async def from_provider(provider: Account | FullNodeClient):
        contract = await Contract.from_address(
            address=REMUS_ADDRESS,
            provider = provider
        )

        return RemusDexView(contract = contract)

    async def get_market_config(self, market_id: int) -> RemusMarketConfig | None:
        """
        Returns RemusMarketConfig for given market_id.
        Fetches values directly from chain.
        """
        config = await self._contract.functions['get_market_config'].call(market_id = market_id)       

        if config[0]['base_token'] == 0:
            return None

        return RemusMarketConfig.from_dict(config[0], market_id=market_id) 
    
    async def get_all_market_configs(self) -> list[RemusMarketConfig | None]:
        """
        Returns all RemusMarketConfigs.
        Fetches values directly from chain.
        """
        configs = await self._contract.functions['get_all_market_configs'].call()

        return [
            RemusMarketConfig.from_dict(cfg = i[1], market_id= i[0])
            for i in configs[0]
        ]
    
    async def get_all_user_orders(self, address: int) -> list[BasicOrder]:
        """
        Returns all user orders, but only those on markets that have preloaded market configs.
        """
        orders = await self._contract.functions['get_all_user_orders'].call(
            user=address
        )

        normalized_orders: list[BasicOrder] = []

        for o in orders[0]:
            market_id = int(o['market_id'])
            market_cfg = get_preloaded_remus_market_config(market_id)
            if market_cfg is None:
                logging.error(f"No market cfg for market id `{market_id}` found, skipping orders.")
                continue
            
            base_token = market_cfg.base_token
            price = Decimal(o['price']) / 10**18

            amount = Decimal(o['amount']) / 10**base_token.decimals
            amount_remaining = Decimal(o['amount_remaining']) / 10**base_token.decimals
            order_id = int(o['order_id'])
            order_side = o['order_side'].variant
            entry_time = int(o['entry_time'])

            new_o = BasicOrder(
                price = price,
                amount = amount,
                amount_remaining = amount_remaining,
                order_id = order_id,
                order_side = order_side,
                entry_time = entry_time,
                market_id = market_id,
                platform = 'Starknet',
                venue = REMUS_IDENTIFIER
            )
            normalized_orders.append(new_o)

        return normalized_orders
    
    async def get_all_user_orders_for_market_id(self, address: int, market_id: int) -> list[BasicOrder]:
        """
        Returns all user orders that are present on market given by market_id
        """
        orders = await self.get_all_user_orders(address)
        
        return [
            o for o in orders
            if o.market_id == market_id
        ]

    async def get_claimable(self, token: StarknetToken, user_address: int) -> Decimal:
        # TODO: Use some class here representing the amount of token that'll include decimals etc
        claimable = await self._contract.functions['get_claimable'].call(
            token_address = token.address,
            user_address = user_address
        )
        return Decimal(claimable[0])

class RemusDexClient:
    address = REMUS_ADDRESS
    """
    Client for interacting with RemusDex.

    This client should be used with single Account only.
    MultiClient will be implemented in the future.
    """
    def __init__(self, contract: Contract):
        self._contract = contract
        self.view = RemusDexView(contract=self._contract)

    @staticmethod
    async def from_account(account: Account) -> "RemusDexClient":
        contract = await Contract.from_address(
            address=REMUS_ADDRESS,
            provider=account
        )

        return RemusDexClient(
            contract = contract
        )


    def prep_claim_call(self, token: StarknetToken, amount: Decimal) -> PreparedFunctionInvokeV3:
        # TODO: Add fees
        return self._contract.functions['claim'].prepare_invoke_v3(
            token_address = token.address,
            amount = int(amount),
        )
    
    def prep_submit_maker_order_call(
            self, 
            order: FutureOrder, 
            market_cfg: RemusMarketConfig, 
    ) -> PreparedFunctionInvokeV3:
        """
        Prepares submit_maker_order Invoke from FutureOrder.
        """
        base_token_decimals = market_cfg.base_token.decimals

        amount_raw = int(order.amount * 10 ** base_token_decimals)
        amount_raw = amount_raw // market_cfg.lot_size
        amount_raw = amount_raw * market_cfg.lot_size

        price_raw = int(order.price * 10**18)
        price_raw = price_raw // market_cfg.tick_size
        price_raw = price_raw * market_cfg.tick_size
        if order.order_side.lower() == 'ask':
            price_raw = price_raw + market_cfg.tick_size

        if order.order_side.lower() == 'ask':
            target_token_address = market_cfg.base_token.address
            order_side = 'Ask'
        else:
            target_token_address = market_cfg.quote_token.address
            order_side = 'Bid'

        return self._contract.functions['submit_maker_order'].prepare_invoke_v3(
            market_id = market_cfg.market_id,
            target_token_address=target_token_address,
            order_price=price_raw,
            order_size=amount_raw,
            order_side=(order_side, None),
            order_type=('Basic', None),
            time_limit=('GTC', None),
        )

    def prep_delete_maker_order_call(
            self, 
            order: BasicOrder, 
    ) -> PreparedFunctionInvokeV3:

        return self._contract.functions['delete_maker_order'].prepare_invoke_v3(
            maker_order_id = order.order_id
        )