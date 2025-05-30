from dataclasses import dataclass
from instrument import Instrument

@dataclass
class StarknetToken(Instrument):
    net: str
    symbol: str
    name: str
    decimals: int
    address: str

# TODO: Once needed, add testnet capabilities
SN_ETH = StarknetToken(
    net = "Starknet",
    symbol = "ETH",
    name = "ETH",
    decimals = 18,
    address = "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"
)

SN_WBTC = StarknetToken(
    net = "Starknet",
    symbol = "WBTC",
    name = "wBTC",
    decimals = 8,
    address = "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac"
)

SN_USDC = StarknetToken(
    net = "Starknet",
    symbol = "USDC",
    name = "USDC",
    decimals = 6,
    address = "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"
)

SN_STRK = StarknetToken(
    net = "Starknet",
    symbol = "STRK",
    name = "STRK",
    decimals = 18,
    address = "0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d"
)

SN_DOG = StarknetToken(
    net = "Starknet",
    symbol = "DOG",
    name = "DOG GO TO THE MOON",
    decimals = 5,
    address = "0x040e81cfeb176bfdbc5047bbc55eb471cfab20a6b221f38d8fda134e1bfffca4"
)

SN_SYMBOL_TO_TOKEN: dict[str, StarknetToken] = {
    "ETH": SN_ETH,
    "WBTC": SN_WBTC,
    "USDC": SN_USDC,
    "STRK": SN_STRK,
    "DOG": SN_DOG
}

def get_sn_token_from_symbol(symbol: str) -> StarknetToken | None:
    return SN_SYMBOL_TO_TOKEN.get(symbol)
