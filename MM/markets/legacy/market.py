import asyncio
from dataclasses import dataclass
from decimal import Decimal
from starknet_py.contract import Contract

from instruments.instrument import Instrument, InstrumentAmount
from marketmaking.order import BasicOrder
from venues.remus.remus_market_configs import RemusMarketConfig
from venues.remus.remus import RemusDexClient




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

    async def get_total_position(self, address: int) -> PositionInfo:
        (
            orders,
            claimable_base,
            claimable_quote,
            balance_base,
            balance_quote,
        ) = await asyncio.gather(
            self.remus_client.view.get_all_user_orders_for_market_id(
                address, self.market_cfg.market_id
            ),
            self.remus_client.view.get_claimable(
                self.market_cfg.base_token, address
            ),
            self.remus_client.view.get_claimable(
                self.market_cfg.quote_token, address
            ),
            self.base_token_contract.functions["balanceOf"].call(account=address),
            self.quote_token_contract.functions["balanceOf"].call(account=address),
        )

        orders_base, orders_quote = _get_base_quote_position_from_active_orders(orders.active.all_orders)

        return PositionInfo(
            balance_base=Decimal(balance_base[0])
            / 10**self.market_cfg.base_token.decimals,
            balance_quote=Decimal(balance_quote[0])
            / 10**self.market_cfg.quote_token.decimals,
            withdrawable_base=claimable_base,
            withdrawable_quote=claimable_quote,
            in_orders_base=orders_base,
            in_orders_quote=orders_quote,
        )


def _get_base_quote_position_from_active_orders(
    orders: list[BasicOrder],
) -> tuple[Decimal, Decimal]:
    base = Decimal(0)
    quote = Decimal(0)

    for o in orders:
        if o.order_side.lower() == "ask":
            base += o.amount_remaining
            continue
        # bid order
        quote += o.amount_remaining * o.price

    return base, quote
