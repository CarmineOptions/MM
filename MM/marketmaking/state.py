from typing import Dict, List


from marketmaking.market import Market
from marketmaking.statemarket import StateMarket
from marketmaking.waccount import WAccount



class State:

    def __init__(self, markets: List[Market], accounts: List[WAccount]) -> None:
        self.market_states: Dict[str, StateMarket] = {
            market.market_id: StateMarket(accounts, market)
            for market in markets
        }
