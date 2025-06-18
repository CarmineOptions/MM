"""
This script is able to manage single Remus market and single account, even thought the MarketMaker
is build for multiple markets and multiple accounts.

Other "deploy scripts" that are yet to be created will be able to manage multiple markets and
multiple accounts.
"""

import time
import asyncio
import logging
import sys

from starknet_py.contract import Contract
from starknet_py.net.client_errors import ClientError
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models.chains import StarknetChainId
from starknet_py.net.signer.key_pair import KeyPair

from marketmaking.orderchain.order_chain import OrderChain
from marketmaking.reconciling import get_reconciler
from oracles.data_sources import get_data_source
from marketmaking.order import BasicOrder
from venues.remus.remus import RemusDexClient
from instruments.starknet import get_sn_token_from_symbol
from cfg.cfg_classes import AccountConfig
from marketmaking.market import Market
from marketmaking.marketmakers.simple_marketmaker import SimpleMarketMaker
from state.state import State
from marketmaking.transaction_builder import TransactionBuilder
from marketmaking.waccount import WAccount
from cfg import load_config
from args import parse_args
from monitoring import metrics

REMUS_ADDRESS = "0x067e7555f9ff00f5c4e9b353ad1f400e2274964ea0942483fae97363fd5d7958"
NETWORK = "MAINNET"


def setup_logging(log_level: str) -> None:
    """Configures logging for the application."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        filename="marketmaker.log", filemode="a", level=logging.INFO, format=log_format
    )
    logging.getLogger("httpx").setLevel(logging.ERROR)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(log_format))

    # Attach to root logger
    logging.getLogger().addHandler(console)
    logging.getLogger().addHandler(metrics.PrometheusMetricsErrorHandler())


def get_account(account_cfg: AccountConfig) -> Account:
    """
    Get a market makers account.

    Raises ValueError if any of needed environment variables is not defined.
    """

    rpc_url = account_cfg.rpc_url
    if rpc_url is None:
        raise ValueError(
            f"No rpc url found from env variable `{account_cfg.rpc_url_env}`"
        )

    wallet_address = account_cfg.wallet_address
    if wallet_address is None:
        raise ValueError(
            f"No wallet address found from env variable `{account_cfg.wallet_address_env}`"
        )

    keystore_path = account_cfg.keystore_path
    if keystore_path is None:
        raise ValueError(
            f"No keystore path found from env variable `{account_cfg.keystore_path_env}`"
        )

    account_password = account_cfg.password
    if account_password is None:
        raise ValueError(
            f"No account password found from env variable `{account_cfg.password_path_env}`"
        )

    client = FullNodeClient(node_url=rpc_url)
    account = Account(
        client=client,
        address=wallet_address,
        key_pair=KeyPair.from_keystore(
            keystore_path,
            account_password.encode(),  # type: ignore
        ),
        chain=StarknetChainId[NETWORK],
    )
    logging.info("Succesfully loaded account.")
    return account


def pretty_print_orders(asks: list[BasicOrder], bids: list[BasicOrder]) -> None:
    logging.info("PRETTY PRINTED CURRENT ORDERS.")
    for ask in sorted(asks, key=lambda x: -x.price):
        logging.info("\t\t%s; %s", ask.price, ask.amount_remaining)
    logging.info("XXX")
    for bid in sorted(bids, key=lambda x: -x.price):
        logging.info("\t\t%s; %s", bid.price, bid.amount_remaining)


async def main() -> None:
    # TODO: Some cfg validaiton (base!=quote, etc)

    metrics.start_metrics_server()

    setup_logging("DEBUG")

    args = parse_args()

    cfg = load_config(args.cfg_path)

    order_chain = OrderChain.from_config(cfg.order_chain)

    reconciler = get_reconciler(cfg.reconciler)

    market_id = cfg.asset.market_id
    account = get_account(cfg.account)
    wrapped_account = WAccount(account=account)

    base_token = get_sn_token_from_symbol(cfg.asset.base_asset)
    if base_token is None:
        raise ValueError(f"Token `{cfg.asset.base_asset}` is not supported")

    quote_token = get_sn_token_from_symbol(cfg.asset.quote_asset)
    if quote_token is None:
        raise ValueError(f"Token `{cfg.asset.quote_asset}` is not supported")

    quote_token_contract = await Contract.from_address(
        address=quote_token.address, provider=account
    )
    base_token_contract = await Contract.from_address(
        address=base_token.address, provider=account
    )

    remus_client = await RemusDexClient.from_account(account=account)
    market_cfg = await remus_client.view.get_market_config(market_id)

    if market_cfg is None:
        raise ValueError(f"Unable to fetch RemusMarketConfig for market_id={market_id}")

    market = Market(
        market_id=cfg.asset.market_id,
        remus_client=remus_client,
        base_token_contract=base_token_contract,
        quote_token_contract=quote_token_contract,
        market_cfg=market_cfg,
    )

    data_source = get_data_source(
        cfg.asset.price_source, cfg.asset.base_asset, cfg.asset.quote_asset
    )
    state = State(
        market=market, account=wrapped_account, fair_price_fetcher=data_source
    )

    transaction_builder = TransactionBuilder(
        remus_client=remus_client,
        market_id=cfg.asset.market_id,
        market_cfg=market_cfg,
        max_fee=0,
    )

    market_maker = SimpleMarketMaker(
        account=wrapped_account,
        market=market,
        order_reconciler=reconciler,
        order_chain=order_chain,
        tx_builder=transaction_builder,
    )

    await market_maker.initialize_trading()

    while True:
        try:
            loop_start_time = time.time()

            await state.update()

            metrics.track_state_update_time(time.time() - loop_start_time)

            logging.info("My current orders: %s", state.account.orders)
            logging.info("Fair price queried: %s.", state.fair_price)
            logging.info("Current position: %s", state.account.position)

            metrics.track_position(state.account.position)

            pretty_print_orders(
                state.account.orders.active.asks, state.account.orders.active.bids
            )

            await market_maker.pulse(state=state)

            logging.info("Pulsed market maker with fair price: %s", state.fair_price)
        except Exception as e:
            # Catching here and not as "except ClientError" because there can be many different ClientErrors
            if isinstance(e, ClientError) and "Account nonce" in e.message:
                logging.error("Account nonce error, trying to reinitialize account...")
                await wrapped_account.reset_latest_nonce()
                logging.info("Reinitialized account.")

            logging.error("Error error occurred: %s", str(e), exc_info=True)
            await asyncio.sleep(5)
            # continue

        metrics.track_loop_time(time.time() - loop_start_time)
        logging.info("Sleeping for 10 seconds before next pulse...")
        await asyncio.sleep(10)


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
