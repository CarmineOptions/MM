
from marketmaking.market import Market
from marketmaking.statemarket import StateMarket


class State:
    # TODO: Add account/portfolio info
    def __init__(self, market: Market) -> None:
        self.market_state = StateMarket(market)