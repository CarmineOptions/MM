
from platforms.starknet.starknet_account import WAccount
from .market import StarknetMarketABC
from .starknet_markets.ekubo_limit_order_market import EkuboLimitOrderMarket
from .starknet_markets.remus_market import RemusMarket
from .starknet_markets.ekubo_clmm_market import EkuboCLMMMarket

async def get_starknet_market(name: str, account: WAccount, market_id: int) -> StarknetMarketABC:
    if name == 'ekubo_clmm':
        return await EkuboCLMMMarket.new(account = account, market_id = market_id)
    if name == 'ekubo_limit_orders':
        return await EkuboLimitOrderMarket.new(account = account, market_id=market_id)
    if name == 'remus':
        return await RemusMarket.new(account = account, market_id = market_id)
    
    raise ValueError(f"Unable to find Starknet market for name `{name}`")
