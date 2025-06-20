
from marketmaking.waccount import WAccount
from .market import Market
from .ekubo_market import EkuboMarket
from .remus_market import RemusMarket

async def get_market(name: str, account: WAccount, market_id: int) -> Market:
    if name == 'ekubo':
        return await EkuboMarket.new(account = account, market_id=market_id)
    if name == 'remus':
        return await RemusMarket.new(account = account, market_id = market_id)
    
    raise ValueError(f"Unable to find connector for unknown venue `{name}`")