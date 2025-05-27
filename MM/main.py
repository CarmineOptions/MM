"""
This script is able to manage single Remus market and single account, even thought the MarketMaker
is build for multiple markets and multiple accounts.

Other "deploy scripts" that are yet to be created will be able to manage multiple markets and
multiple accounts.
"""
import asyncio
import logging
import requests
import sys

from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.models.chains import StarknetChainId

from oracles.simple_prices import get_price_fetcher
from marketmaking.market import Market
from marketmaking.marketmaker import MarketMaker
from marketmaking.pocmmmodel import POCMMModel
from marketmaking.state import State
from marketmaking.statemarket import StateMarket
from marketmaking.transaction_builder import TransactionBuilder
from marketmaking.waccount import WAccount



REMUS_ADDRESS = '0x067e7555f9ff00f5c4e9b353ad1f400e2274964ea0942483fae97363fd5d7958'
BASE_TOKEN_ADDRESS = 0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7
QUOTE_TOKEN_ADDRESS = 0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8

RPC_URL = "https://starknet-mainnet.public.blastapi.io/rpc/v0_7"
WALLET_ADDRESS = "0x463de332da5b88a1676bfb4671dcbe4cc1a9147c46300a1658ed43a22d830c3"


ACCOUNT_PASSWORD=''
PATH_TO_KEYSTORE="keystore.json"
NETWORK='MAINNET'

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



def get_account() -> Account:
    """Get a market makers account."""
    client = FullNodeClient(node_url=RPC_URL)
    account = Account(
        client = client,
        address = WALLET_ADDRESS,
        key_pair = KeyPair.from_keystore(PATH_TO_KEYSTORE, ACCOUNT_PASSWORD),
        chain = StarknetChainId[NETWORK]
    )
    logging.info("Succesfully loaded account.")
    return account


def pretty_print_orders(asks, bids):
    logging.info('PRETTY PRINTED CURRENT ORDERS.')
    for ask in sorted(asks, key=lambda x: -x['price']):
        logging.info('\t\t%s; %s', ask['price'] / 10**18, ask['amount_remaining'] / 10**18)
    logging.info('XXX')
    for bid in sorted(bids, key=lambda x: -x['price']):
        logging.info('\t\t%s; %s', bid['price'] / 10**18, bid['amount_remaining'] / 10**18)


async def main():
    setup_logging('DEBUG')
    
    account = get_account()

    wrapped_account = WAccount(account=account)

    quote_token_contract = await Contract.from_address(
        address=QUOTE_TOKEN_ADDRESS,
        provider=account
    )
    base_token_contract = await Contract.from_address(
        address=BASE_TOKEN_ADDRESS,
        provider=account
    )
    dex_contract = await Contract.from_address(
        address=REMUS_ADDRESS,
        provider=account
    )

    # configs - FIXME: should be in a config file
    all_remus_cfgs = await dex_contract.functions['get_all_market_configs'].call()
    market_id = 1
    market_cfg = [x for x in all_remus_cfgs[0] if x[0] == market_id][0]
    market_maker_cfg = {
                'target_relative_distance_from_FP': 0.001, # where best order is created 
                'max_relative_distance_from_FP': 0.003, # too far from FP to be considered best (it is considered deep)
                'min_relative_distance_from_FP': 0.0005, # too close to FP to exist -> if closer kill the order

                'order_dollar_size': 200 * 10**18,  # in $
                'minimal_remaining_quote_size': 100,  # in $
                'max_number_of_orders_per_side': 3,

                'max_fee': 9122241938326667
            }
    
    market = Market(
            market_id=1,
            dex_contract=dex_contract,
            base_token_contract=base_token_contract,
            quote_token_contract=quote_token_contract,
            dex_address=REMUS_ADDRESS,
            base_token_address=BASE_TOKEN_ADDRESS,
            quote_token_address=QUOTE_TOKEN_ADDRESS,
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
        market_id=market_id,
        market_cfg=market_cfg,
        max_fee=market_maker_cfg['max_fee']
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

    get_price = get_price_fetcher(market_id)

    await market_maker.initialize_trading()

    while True:
        for market_id in [1]:
            try:

                logging.info('Claiming tokens for market_id: %s', market_id)
                await market_maker.claim_tokens(market_id=1)
                logging.info('Claimed tokens for market_id: %s', market_id)

                # Get my orders from the market and pulse them.
                my_orders = await dex_contract.functions['get_all_user_orders'].call(
                    user=wrapped_account.account.address
                )
                bids = [x for x in my_orders[0] if x['market_id'] == market_id and x['order_side'].variant == 'Bid']
                asks = [x for x in my_orders[0] if x['market_id'] == market_id and x['order_side'].variant == 'Ask']
                bids = sorted(bids, key = lambda x: -x['price'])
                asks = sorted(asks, key = lambda x: -x['price'])
                logging.info('My current orders: %s, %s.', bids, asks)
                await market_maker.pulse(data = {
                    'type': 'my_orders_snapshot',
                    'market_id': 1,
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
                    'market_id': 1,
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
