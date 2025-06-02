
from dataclasses import dataclass
import logging

from instruments.starknet import SN_ETH, SN_STRK, SN_USDC, SN_WBTC, StarknetToken, get_sn_token_from_address, SN_DOG


@dataclass
class RemusFeesConfig:
    taker_fee_bps: int
    maker_fee_bps: int

    @staticmethod
    def from_dict(fees: dict) -> "RemusFeesConfig":
        return RemusFeesConfig(
            taker_fee_bps = fees['taker_fee_bps'],
            maker_fee_bps = fees['maker_fee_bps']
        )

@dataclass
class RemusMarketConfig:
    market_id: int
    base_token: StarknetToken
    quote_token: StarknetToken
    tick_size: int
    lot_size: int
    trading_enabled: bool
    fees: RemusFeesConfig

    @staticmethod
    def from_dict(cfg: dict, market_id: int) -> "RemusMarketConfig | None":
        base_token = get_sn_token_from_address(cfg['base_token'])
        quote_token = get_sn_token_from_address(cfg['quote_token'])
        
        if base_token is None or quote_token is None:
            logging.error(f"Unable to find tokens for base/quote: {cfg['base_token']}/{cfg['quote_token']}, market_id: {market_id}")
            return None

        return RemusMarketConfig(
            market_id = market_id,
            base_token = base_token,
            quote_token = quote_token,
            tick_size = cfg['tick_size'],
            lot_size = cfg['lot_size'],
            trading_enabled = cfg['trading_enabled'],
            fees = RemusFeesConfig.from_dict(cfg['fees'])
        )
    

ETH_USDC_MC = RemusMarketConfig(
    market_id = 1,
    base_token = SN_ETH,
    quote_token = SN_USDC,
    tick_size = 100000000000000000,
    lot_size = 1000000000000000,
    trading_enabled = True,
    fees = RemusFeesConfig(
        taker_fee_bps=0,
        maker_fee_bps=0
    )
)

STRK_USDC_MC = RemusMarketConfig(
    market_id=2,
    base_token=SN_STRK,
    quote_token=SN_USDC,
    tick_size=100000000000000,
    lot_size=1000000000000000000,
    trading_enabled=True,
    fees=RemusFeesConfig(
        taker_fee_bps=0,
        maker_fee_bps=0
    )
)

WBTC_USDC_MC = RemusMarketConfig(
    market_id=3,
    base_token=SN_WBTC,
    quote_token=SN_USDC,
    tick_size=1000000000000000000,
    lot_size=10000,
    trading_enabled=True,
    fees=RemusFeesConfig(
        taker_fee_bps=0,
        maker_fee_bps=0
    )
)

WBTC_DOG_MC = RemusMarketConfig(
    market_id=11,
    base_token=SN_WBTC,
    quote_token=SN_DOG,
    tick_size=10000000000000000000,
    lot_size=1000,
    trading_enabled=True,
    fees=RemusFeesConfig(
        taker_fee_bps=0,
        maker_fee_bps=0)
)

MARKET_ID_TO_CONFIG: dict[int, RemusMarketConfig] = {
    1: ETH_USDC_MC,
    2: STRK_USDC_MC,
    3: WBTC_USDC_MC,
    11: WBTC_DOG_MC
}

def get_preloaded_remus_market_config(market_id: int) -> RemusMarketConfig | None:
    return MARKET_ID_TO_CONFIG.get(market_id)