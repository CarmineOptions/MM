from dataclasses import dataclass
from decimal import Decimal
from starknet_py.contract import Contract

from marketmaking.order import BasicOrder
from venues.remus.remus_market_configs import RemusMarketConfig
from venues.remus.remus import RemusDexClient


@dataclass
class PositionInfo:
    balance_base: Decimal
    balance_quote: Decimal

    claimable_base: Decimal
    claimable_quote: Decimal

    in_orders_base: Decimal
    in_orders_quote: Decimal

    @property
    def total_base(self) -> Decimal:
        return self.balance_base + self.claimable_base + self.in_orders_base

    @property
    def total_quote(self) -> Decimal:
        return self.balance_quote + self.claimable_quote + self.in_orders_quote
class Market:
    """
    Describes the market and it's parameters.

    Has the all of the contracts needed to interact with the market.
    """

    def __init__(
        self,
        market_id: int,
        remus_client: RemusDexClient,
        base_token_contract: Contract,
        quote_token_contract: Contract,
        market_cfg: RemusMarketConfig,
    ) -> None:
        self.market_id = market_id

        self.remus_client = remus_client
        self.base_token_contract = base_token_contract
        self.quote_token_contract = quote_token_contract

        self.market_cfg = market_cfg

    def restart_contracts(self) -> None:
        """
        Restart the contracts for the market.
        This method should be called to restart the contracts for the market.
        """
        # FIXME
        pass
    
    async def _get_total_position(self, address: int) -> PositionInfo:
        orders = await self.remus_client.view.get_all_user_orders_for_market_id(address, self.market_cfg.market_id)
        orders_base, orders_quote = _get_base_quote_position_from_orders(orders)

        claimable_base = await self.remus_client.view.get_claimable_hr(self.market_cfg.base_token, address)
        claimable_quote = await self.remus_client.view.get_claimable_hr(self.market_cfg.quote_token, address)

        balance_base = await self.base_token_contract.functions['balanceOf'].call(
            account = address
        )
        balance_quote = await self.quote_token_contract.functions['balanceOf'].call(
            account = address
        )
        
        return PositionInfo(
            balance_base = balance_base[0] / 10 **self.market_cfg.base_token.decimals,
            balance_quote = balance_quote[0] / 10 **self.market_cfg.quote_token.decimals,
            
            claimable_base = claimable_base,
            claimable_quote = claimable_quote,

            in_orders_base=orders_base,
            in_orders_quote=orders_quote
        )

def _get_base_quote_position_from_orders(orders: list[BasicOrder]) -> tuple[Decimal, Decimal]:
    base = Decimal(0)
    quote = Decimal(0)

    for o in orders:
        if o.order_side.lower() == 'ask':
            base += o.amount_remaining
            continue
        # bid order
        quote += o.amount_remaining * o.price

    return base, quote