from dataclasses import dataclass
from instruments.instrument import Instrument


@dataclass
class StarknetToken(Instrument):
    platform: str
    symbol: str
    name: str
    decimals: int
    address: int


# TODO: Once needed, add testnet capabilities
SN_ETH = StarknetToken(
    platform="Starknet",
    symbol="ETH",
    name="ETH",
    decimals=18,
    address=0x049D36570D4E46F48E99674BD3FCC84644DDD6B96F7C741B1562B82F9E004DC7,
)

SN_WBTC = StarknetToken(
    platform="Starknet",
    symbol="WBTC",
    name="wBTC",
    decimals=8,
    address=0x03FE2B97C1FD336E750087D68B9B867997FD64A2661FF3CA5A7C771641E8E7AC,
)

SN_USDC = StarknetToken(
    platform="Starknet",
    symbol="USDC",
    name="USDC",
    decimals=6,
    address=0x053C91253BC9682C04929CA02ED00B3E423F6710D2EE7E0D5EBB06F3ECF368A8,
)

SN_STRK = StarknetToken(
    platform="Starknet",
    symbol="STRK",
    name="STRK",
    decimals=18,
    address=0x04718F5A0FC34CC1AF16A1CDEE98FFB20C31F5CD61D6AB07201858F4287C938D,
)

SN_DOG = StarknetToken(
    platform="Starknet",
    symbol="DOG",
    name="DOG GO TO THE MOON",
    decimals=5,
    address=0x040E81CFEB176BFDBC5047BBC55EB471CFAB20A6B221F38D8FDA134E1BFFFCA4,
)

SN_SYMBOL_TO_TOKEN: dict[str, StarknetToken] = {
    "ETH": SN_ETH,
    "WBTC": SN_WBTC,
    "USDC": SN_USDC,
    "STRK": SN_STRK,
    "DOG": SN_DOG,
}

SN_ADDRESS_TO_TOKEN: dict[int, StarknetToken] = {
    value.address: value for value in SN_SYMBOL_TO_TOKEN.values()
}


def get_sn_token_from_symbol(symbol: str) -> StarknetToken | None:
    return SN_SYMBOL_TO_TOKEN.get(symbol)


def get_sn_token_from_address(address: int) -> StarknetToken | None:
    return SN_ADDRESS_TO_TOKEN.get(address)
