
from platforms.starknet.starknet_account import WAccount
from .market import Market
from .ekubo_limit_order_market import EkuboLimitOrderMarket
from .remus_market import RemusMarket
from .ekubo_clmm_market import EkuboCLMMMarket

async def get_market(name: str, account: WAccount, market_id: int) -> Market:
    if name == 'ekubo_clmm':
        return await EkuboCLMMMarket.new(account = account, market_id = market_id)
    if name == 'ekubo_limit_orders':
        return await EkuboLimitOrderMarket.new(account = account, market_id=market_id)
    if name == 'remus':
        return await RemusMarket.new(account = account, market_id = market_id)
    
    raise ValueError(f"Unable to find connector for unknown venue `{name}`")