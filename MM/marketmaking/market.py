from starknet_py.contract import Contract

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
