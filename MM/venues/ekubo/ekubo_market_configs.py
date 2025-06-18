

from dataclasses import dataclass

from instruments.starknet import SN_ETH, SN_STRK, SN_USDC, SN_WBTC, StarknetToken

EKUBO_LIMIT_ORDER_TICK_SPACING = 128

@dataclass
class EkuboMarketConfig:
    market_id: int
    token0: StarknetToken
    token1: StarknetToken
    tick_spacing: int 

ETH_USDC_LIMIT_MC = EkuboMarketConfig(
    market_id = 1,
    token0 = SN_ETH,
    token1 = SN_USDC,
    tick_spacing=EKUBO_LIMIT_ORDER_TICK_SPACING
)

STRK_USDC_LIMIT_MC = EkuboMarketConfig(
    market_id = 2,
    token0=SN_STRK,
    token1=SN_USDC,
    tick_spacing=EKUBO_LIMIT_ORDER_TICK_SPACING
)

WBTC_USDC_LIMIT_MC = EkuboMarketConfig(
    market_id = 3,
    token0=SN_WBTC,
    token1=SN_USDC,
    tick_spacing=EKUBO_LIMIT_ORDER_TICK_SPACING
)


MARKET_ID_TO_CONFIG: dict[int, EkuboMarketConfig] = {
    1: ETH_USDC_LIMIT_MC,
    2: STRK_USDC_LIMIT_MC,
    3: WBTC_USDC_LIMIT_MC,
}

def get_preloaded_ekubo_market_config(market_id: int) -> EkuboMarketConfig | None:
    return MARKET_ID_TO_CONFIG.get(market_id)