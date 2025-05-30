from dataclasses import dataclass
from decimal import Decimal
import logging
from typing import OrderedDict

from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.contract import Contract, PreparedFunctionInvokeV3


from instruments.instrument import InstrumentAmount
from marketmaking.order import BasicOrder
from instruments.starknet import StarknetToken, get_sn_token_from_address

REMUS_ADDRESS = '0x067e7555f9ff00f5c4e9b353ad1f400e2274964ea0942483fae97363fd5d7958'

@dataclass
class RemusFeesConfig:
    taker_fee_bps: int
    maker_fee_bps: int

    @staticmethod
    def from_dict(fees: dict) -> "RemusFeesConfig":
        return RemusFeesConfig(
            taker_fee_bps = fees['taker_fee_bps'],
            maker_fee_bps = fees['maker_fee_bps']
        )

@dataclass
class RemusMarketConfig:
    market_id: int
    base_token: StarknetToken
    quote_token: StarknetToken
    tick_size: int
    lot_size: int
    trading_enabled: bool
    fees: RemusFeesConfig

    @staticmethod
    def from_dict(cfg: dict, market_id: int) -> "RemusMarketConfig | None":
        base_token = get_sn_token_from_address(cfg['base_token'])
        quote_token = get_sn_token_from_address(cfg['quote_token'])
        
        if base_token is None or quote_token is None:
            logging.error(f"Unable to find tokens for base/quote: {cfg['base_token']}/{cfg['quote_token']}, market_id: {market_id}")
            return None

        return RemusMarketConfig(
            market_id = market_id,
            base_token = base_token,
            quote_token = quote_token,
            tick_size = cfg['tick_size'],
            lot_size = cfg['lot_size'],
            trading_enabled = cfg['trading_enabled'],
            fees = RemusFeesConfig.from_dict(cfg['fees'])
        )

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
        Returns RemusMarketConfig for given market_id
        """
        config = await self._contract.functions['get_market_config'].call(market_id = market_id)       

        if config[0]['base_token'] == 0:
            return None

        return RemusMarketConfig.from_dict(config[0], market_id=market_id) 
    
    async def get_all_user_orders(self, address: int) -> list[BasicOrder]:
        """
        Returns all user orders.
        """
        orders = await self._contract.functions['get_all_user_orders'].call(
            user=address
        )

        return [
            BasicOrder.from_remus_order(orders[0])
        ]
    
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
    """
    Client for interacting with RemusDex. 

    This client should be used with single Account only. 
    MultiClient will be implemented in the future.
    """
    async def __init__(self, account: Account):
        self._contract = await Contract.from_address(
            address = REMUS_ADDRESS,
            provider = account
        )
        self.view = RemusDexView(provider = account)

    async def get_claim_call(self, token: StarknetToken, amount: Decimal, nonce: int | None) -> PreparedFunctionInvokeV3 | None:
        if amount <= 0:
            return None
        
        if nonce is not None:
            call = self._contract.functions['claim'].prepare_invoke_v3(
                token_address = token.address,
                amount = int(amount),
                nonce = nonce,
                auto_estimate=True
            )
        else: 
            call = self._contract.functions['claim'].prepare_invoke_v3(
                token_address = token.address,
                amount = int(amount),
                auto_estimate=True
            )
        
        return call
