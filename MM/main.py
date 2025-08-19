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
import pprint


from platforms.starknet.starknet_platform import StarknetPlatform
from marketmaking.orderchain.order_chain import OrderChain
from marketmaking.reconciling import get_reconciler
from oracles.data_sources import get_data_source
from marketmaking.order import BasicOrder
from marketmaking.marketmakers.simple_marketmaker import SimpleMarketMaker
from state.state import State
from cfg import load_config
from args import parse_args
from monitoring import metrics


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




def pretty_print_orders(asks: list[BasicOrder], bids: list[BasicOrder]) -> None:
    logging.info("PRETTY PRINTED CURRENT ORDERS.")
    for ask in sorted(asks, key=lambda x: -x.price):
        logging.info("\t\t%s; %s", ask.price, ask.amount_remaining)
    logging.info("XXX")
    for bid in sorted(bids, key=lambda x: -x.price):
        logging.info("\t\t%s; %s", bid.price, bid.amount_remaining)


async def main() -> None:

    metrics.start_metrics_server()

    setup_logging("DEBUG")

    args = parse_args()

    cfg = load_config(args.cfg_path)

    logging.info(f"Loaded config:\n {pprint.pformat(dict(cfg))}")

    order_chain = OrderChain.from_config(cfg.order_chain)

    reconciler = get_reconciler(cfg.reconciler)

    platform = await StarknetPlatform.from_config(cfg = cfg)

    data_source = get_data_source(
        cfg.price_source.price_source, cfg.price_source.base_asset, cfg.price_source.quote_asset
    )
    state = State(
        market=platform._market, 
        account=platform._waccount, 
        fair_price_fetcher=data_source
    )
    
    market_maker = SimpleMarketMaker(
        market=platform.market,
        order_reconciler=reconciler,
        order_chain=order_chain,
    )

    await platform.initialize_trading()

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

            prologue, reconciled_orders = await market_maker.pulse(state=state)
            
            await platform.execute_operations(state = state, prologue=prologue, ops = reconciled_orders)

            logging.info("Pulsed market maker with fair price: %s", state.fair_price)
        except Exception as e:

            if not await platform.error_handled(e):
                logging.error("Unhandled error occurred: %s", str(e), exc_info=True)

            await asyncio.sleep(5)

        metrics.track_loop_time(time.time() - loop_start_time)
        logging.info("Sleeping for 10 seconds before next pulse...")
        await asyncio.sleep(10)


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
