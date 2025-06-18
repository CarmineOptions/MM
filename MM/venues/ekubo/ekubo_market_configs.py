

from dataclasses import dataclass

from instruments.starknet import SN_ETH, SN_STRK, SN_USDC, SN_WBTC, StarknetToken
from markets.market import MarketConfig

EKUBO_LIMIT_ORDER_TICK_SPACING = 128

@dataclass
class EkuboMarketConfig(MarketConfig):
    tick_spacing: int 

ETH_USDC_LIMIT_MC = EkuboMarketConfig(
    market_id = 1,
    base_token = SN_ETH,
    quote_token = SN_USDC,
    tick_spacing=EKUBO_LIMIT_ORDER_TICK_SPACING
)

STRK_USDC_LIMIT_MC = EkuboMarketConfig(
    market_id = 2,
    base_token=SN_STRK,
    quote_token=SN_USDC,
    tick_spacing=EKUBO_LIMIT_ORDER_TICK_SPACING
)

WBTC_USDC_LIMIT_MC = EkuboMarketConfig(
    market_id = 3,
    base_token=SN_WBTC,
    quote_token=SN_USDC,
    tick_spacing=EKUBO_LIMIT_ORDER_TICK_SPACING
)


MARKET_ID_TO_CONFIG: dict[int, EkuboMarketConfig] = {
    1: ETH_USDC_LIMIT_MC,
    2: STRK_USDC_LIMIT_MC,
    3: WBTC_USDC_LIMIT_MC,
}

def get_preloaded_ekubo_market_config(market_id: int) -> EkuboMarketConfig | None:
    return MARKET_ID_TO_CONFIG.get(market_id)