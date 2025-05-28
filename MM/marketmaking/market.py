from starknet_py.contract import Contract



class Market:
    """
    Describes the market and it's parameters.

    Has the all of the contracts needed to interact with the market.
    """

    def __init__(
            self,
            market_id: int,
            dex_contract: Contract,
            base_token_contract: Contract,
            quote_token_contract: Contract,
            dex_address: str,
            base_token_address: int,
            quote_token_address: int,
    ) -> None:
        self.market_id = market_id

        self.dex_contract = dex_contract
        self.base_token_contract = base_token_contract
        self.quote_token_contract = quote_token_contract

        self.dex_address = dex_address
        self.base_token_address = base_token_address
        self.quote_token_address = quote_token_address
    
    def restart_contracts(self) -> None:
        """
        Restart the contracts for the market.
        This method should be called to restart the contracts for the market.
        """
        # FIXME
        pass
