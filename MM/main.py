"""
This script is able to manage single Remus market and single account, even thought the MarketMaker
is build for multiple markets and multiple accounts.

Other "deploy scripts" that are yet to be created will be able to manage multiple markets and
multiple accounts.
"""
from dotenv import load_dotenv
import asyncio
import logging
import requests
import sys
import os

from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.signer.key_pair import KeyPair
from starknet_py.net.models.chains import StarknetChainId

from instruments.starknet import get_sn_token_from_symbol
from cfg.cfg_classes import AccountConfig
from oracles.simple_prices import get_price_fetcher
from marketmaking.market import Market
from marketmaking.marketmaker import MarketMaker
from marketmaking.pocmmmodel import POCMMModel
from marketmaking.state import State
from marketmaking.statemarket import StateMarket
from marketmaking.transaction_builder import TransactionBuilder
from marketmaking.waccount import WAccount
from marketmaking.order import BasicOrder
from cfg import load_config
from args import parse_args

load_dotenv()

REMUS_ADDRESS = '0x067e7555f9ff00f5c4e9b353ad1f400e2274964ea0942483fae97363fd5d7958'
NETWORK='MAINNET'


# BASE_TOKEN_ADDRESS = 0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac # DOG
# QUOTE_TOKEN_ADDRESS = 0x040e81cfeb176bfdbc5047bbc55eb471cfab20a6b221f38d8fda134e1bfffca4 # wBTC

def setup_logging(log_level: str):
    """Configures logging for the application."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        filename='marketmaker.log',
        filemode='a',
        level=logging.INFO,
        format=log_format
    )
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(log_format))

    # Attach to root logger
    logging.getLogger().addHandler(console)


def get_account(account_cfg: AccountConfig) -> Account:
    """
    Get a market makers account.

    Raises ValueError if any of needed environment variables is not defined.
    """

    rpc_url = account_cfg.rpc_url
    if rpc_url is None:
        raise ValueError(f"No rpc url found from env variable `{account_cfg.rpc_url_env}`")
    
    wallet_address = account_cfg.wallet_address
    if wallet_address is None:
        raise ValueError(f"No wallet address found from env variable `{account_cfg.wallet_address_env}`")

    keystore_path = account_cfg.keystore_path
    if keystore_path is None:
        raise ValueError(f"No keystore path found from env variable `{account_cfg.keystore_path_env}`")

    account_password = account_cfg.account_password
    if account_password is None:
        raise ValueError(f"No account password found from env variable `{account_cfg.account_password_env}`")


    client = FullNodeClient(node_url=rpc_url) 
    account = Account(
        client = client,
        address = wallet_address,
        key_pair = KeyPair.from_keystore(
            keystore_path, 
            account_password.encode() # type: ignore
        ),
        chain = StarknetChainId[NETWORK]
    )
    logging.info("Succesfully loaded account.")
    return account


def pretty_print_orders(asks, bids):
    logging.info('PRETTY PRINTED CURRENT ORDERS.')
    for ask in sorted(asks, key=lambda x: -x.price):
        logging.info('\t\t%s; %s', ask.price / 10**18, ask.amount_remaining / 10**18)
    logging.info('XXX')
    for bid in sorted(bids, key=lambda x: -x.price):
        logging.info('\t\t%s; %s', bid.price / 10**18, bid.amount_remaining / 10**18)


async def main():
    # TODO: Somf cfg validaiton (base!=quote, etc)
    
    setup_logging('DEBUG')

    args = parse_args()

    cfg = load_config(args.cfg_path)

    account = get_account(cfg.account)
    wrapped_account = WAccount(account=account)


    base_token = get_sn_token_from_symbol(cfg.asset.base_asset)
    if base_token is None:
        raise ValueError(f"Token `{cfg.asset.base_asset}` is not supported")

    quote_token = get_sn_token_from_symbol(cfg.asset.quote_asset)
    if quote_token is None:
        raise ValueError(f"Token `{cfg.asset.quote_asset}` is not supported")

    base_token_address = int(base_token.address, 0)
    quote_token_address = int(quote_token.address, 0)

    quote_token_contract = await Contract.from_address(
        address=quote_token_address,
        provider=account
    )
    base_token_contract = await Contract.from_address(
        address=base_token_address,
        provider=account
    )
    dex_contract = await Contract.from_address(
        address=REMUS_ADDRESS,
        provider=account
    )
    # configs - FIXME: should be in a config file
    all_remus_cfgs = await dex_contract.functions['get_all_market_configs'].call()
    market_cfg = [x for x in all_remus_cfgs[0] if x[0] == cfg.asset.market_id][0][1]

    if market_cfg['base_token'] != base_token_address:
        raise ValueError("Base token and market config base token mismatch")

    if market_cfg['quote_token'] != quote_token_address:
        raise ValueError("Quote token and market config base token mismatch")
    
    market_maker_cfg = cfg.marketmaker
    
    market = Market(
            market_id=cfg.asset.market_id,
            dex_contract=dex_contract,
            base_token_contract=base_token_contract,
            quote_token_contract=quote_token_contract,
            dex_address=REMUS_ADDRESS,
            base_token_address=int(base_token_address),
            quote_token_address=int(quote_token_address),
    )

    state = State(markets=[market], accounts=[wrapped_account])
    state_market = state.market_states[market.market_id]

    poc_mm_model = POCMMModel(
        state_market=state_market,
        market_cfg=market_cfg,
        market_maker_cfg=market_maker_cfg
    )

    transaction_builder = TransactionBuilder(
        dex_contract=dex_contract,
        market_id=cfg.asset.market_id,
        market_cfg=market_cfg,
        max_fee=0
    )

    market_maker = MarketMaker(
        accounts=[wrapped_account],
        markets=[market],
        account_market_pairs={wrapped_account: [market]},
        state=state,
        mm_model=poc_mm_model,
        reconciler=None, # TODO:
        claim_rule=None,
        transaction_builder=transaction_builder,
        blockchain_connectors=None
    )

    market_id = cfg.asset.market_id

    get_price = get_price_fetcher(cfg.asset.market_id)

    await market_maker.initialize_trading()

    logging.warning("!!! Make sure `base_decimals` in pocmmmodel.py are correct !!!")
    # await asyncio.sleep(5)


    while True:
        try:

            logging.info('Claiming tokens for market_id: %s', market_id)
            await market_maker.claim_tokens(market_id=market_id)
            logging.info('Claimed tokens for market_id: %s', market_id)

            # Get my orders from the market and pulse them.
            my_orders = await dex_contract.functions['get_all_user_orders'].call(
                user=wrapped_account.account.address
            )
            bids = [x for x in my_orders[0] if x['market_id'] == market_id and x['order_side'].variant == 'Bid']
            asks = [x for x in my_orders[0] if x['market_id'] == market_id and x['order_side'].variant == 'Ask']
            bids = sorted(bids, key = lambda x: -x['price'])
            asks = sorted(asks, key = lambda x: -x['price'])
            bids = [
                BasicOrder.from_remus_order(o)
                for o in bids
            ]
            asks = [
                BasicOrder.from_remus_order(o)
                for o in asks
            ]

            logging.info('My current orders: %s, %s.', bids, asks)
            await market_maker.pulse(data = {
                'type': 'my_orders_snapshot',
                'market_id': market_id,
                'data': {'bids': bids, 'asks': asks},
                'account': wrapped_account.account.address
            })
            logging.info('Pulsed market maker with my orders: %s, %s.', bids, asks)

            # Get current oracle price and pulse it.
            fair_price  = get_price()
            logging.info('Fair price queried: %s.', fair_price)

            pretty_print_orders(asks, bids)

            logging.info('Pulsing market maker with fair price: %s', fair_price)
            await market_maker.pulse(data = {
                'type': 'custom_oracle',
                'market_id': market_id,
                'data': {'price': fair_price},
            })
            logging.info('Pulsed market maker with fair price: %s', fair_price)
        except Exception as e:
            logging.error("Error error occurred: %s", str(e), exc_info=True)
            await asyncio.sleep(5)
            sys.exit(1)
            # continue

        logging.info('Sleeping for 10 seconds before next pulse...')
        await asyncio.sleep(10)


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
