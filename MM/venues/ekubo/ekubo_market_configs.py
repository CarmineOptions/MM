

from dataclasses import dataclass

from instruments.starknet import SN_ETH, SN_STRK, SN_USDC, SN_WBTC, SN_DOG
from markets.market import MarketConfig

EKUBO_LIMIT_ORDER_TICK_SPACING = 128

@dataclass
class EkuboMarketConfig(MarketConfig):
    tick_spacing: int 
    fee: int

ETH_USDC_LIMIT_MC = EkuboMarketConfig(
    market_id = 1,
    base_token = SN_ETH,
    quote_token = SN_USDC,
    tick_spacing=EKUBO_LIMIT_ORDER_TICK_SPACING,
    fee = 0
)

STRK_USDC_LIMIT_MC = EkuboMarketConfig(
    market_id = 2,
    base_token=SN_STRK,
    quote_token=SN_USDC,
    tick_spacing=EKUBO_LIMIT_ORDER_TICK_SPACING,
    fee = 0
)

WBTC_USDC_LIMIT_MC = EkuboMarketConfig(
    market_id = 3,
    base_token=SN_WBTC,
    quote_token=SN_USDC,
    tick_spacing=EKUBO_LIMIT_ORDER_TICK_SPACING,
    fee = 0
)

WBTC_DOG_LIMIT_MC = EkuboMarketConfig(
    market_id = 11,
    base_token = SN_WBTC,
    quote_token = SN_DOG,
    tick_spacing=EKUBO_LIMIT_ORDER_TICK_SPACING,
    fee = 0
)


MARKET_ID_TO_LIMIT_ORDER_CONFIG: dict[int, EkuboMarketConfig] = {
    1: ETH_USDC_LIMIT_MC,
    2: STRK_USDC_LIMIT_MC,
    3: WBTC_USDC_LIMIT_MC,
    11: WBTC_DOG_LIMIT_MC
}

ETH_USDC_CLMM_MC = EkuboMarketConfig(
    market_id = 1,
    base_token = SN_ETH,
    quote_token = SN_USDC,
    tick_spacing = 0x3e8,
    fee = 0x20c49ba5e353f80000000000000000
) 

STRK_USDC_CLMM_MC = EkuboMarketConfig(
    market_id = 2,
    base_token = SN_STRK,
    quote_token = SN_USDC,
    tick_spacing = 1,
    fee = 0
) 


MARKET_ID_TO_CLMM_CONFIG: dict[int, EkuboMarketConfig] = {
    1: ETH_USDC_CLMM_MC,
    2: STRK_USDC_CLMM_MC
}


def get_preloaded_ekubo_limit_order_market_config(market_id: int) -> EkuboMarketConfig | None:
    return MARKET_ID_TO_LIMIT_ORDER_CONFIG.get(market_id)

def get_preloaded_ekubo_clmm_market_config(market_id: int) -> EkuboMarketConfig | None:
    return MARKET_ID_TO_CLMM_CONFIG.get(market_id)