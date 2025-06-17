

from dataclasses import dataclass

from instruments.starknet import SN_ETH, SN_STRK, SN_USDC, SN_WBTC, StarknetToken

EKUBO_LIMIT_ORDER_TICK_SPACING = 128

@dataclass
class EkuboMarketConfig:
    token0: StarknetToken
    token1: StarknetToken
    tick_spacing: int 

ETH_USDC_LIMIT_MC = EkuboMarketConfig(
    token0 = SN_ETH,
    token1 = SN_USDC,
    tick_spacing=EKUBO_LIMIT_ORDER_TICK_SPACING
)

WBTC_USDC_LIMIT_MC = EkuboMarketConfig(
    token0=SN_WBTC,
    token1=SN_USDC,
    tick_spacing=EKUBO_LIMIT_ORDER_TICK_SPACING
)

STRK_USDC_LIMIT_MC = EkuboMarketConfig(
    token0=SN_STRK,
    token1=SN_USDC,
    tick_spacing=EKUBO_LIMIT_ORDER_TICK_SPACING
)
