'''
This module provides Prometheus metrics for monitoring the bot's performance and state.
'''

from decimal import Decimal
from prometheus_client import Counter, Gauge, start_http_server
import logging
import time

from state.account_state import PositionInfo
from marketmaking.reconciling.order_reconciler import ReconciledOrders


def start_metrics_server(port: int = 8000) -> None:
    '''
    Starts a Prometheus metrics server on the specified port.
    '''
    start_http_server(port)


last_error_gauge = Gauge(
    "last_error_timestamp", "Timestamp (in seconds) of the last error that occurred"
)

loop_time = Gauge(
    "loop_time", "Time (in seconds) it took the bot to complete one single loop"
)

state_update_time = Gauge(
    "state_update_time", "Time (in seconds) it took to update the state"
)

total_orders_sent = Counter("total_orders_sent", "Total number of orders sent")

total_orders_canceled = Counter(
    "total_orders_canceled", "Total amount of orders that was sent"
)

current_position_base = Gauge("current_position_base", "Current position in base token")
current_position_quote = Gauge(
    "current_position_quote", "Current position in quote token"
)

current_spread = Gauge("current_spread", "Current quoted spread")
current_fp = Gauge("current_fair_price", "Current fair price")
current_best_ask_price = Gauge("current_best_ask_price", "Current best ask price")
current_best_bid_price = Gauge("current_best_bid_price", "Current best bid price")
current_best_ask_amount = Gauge("current_best_ask_amount", "Current best ask amount")
current_best_bid_amount = Gauge("current_best_bid_amount", "Current best bid amount")

class PrometheusMetricsErrorHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            last_error_gauge.set(int(time.time()))


def track_loop_time(interval: float) -> None:
    loop_time.set(interval)


def track_state_update_time(interval: float) -> None:
    state_update_time.set(interval)


def track_orders_sent(val: int) -> None:
    total_orders_sent.inc(val)


def track_orders_canceled(val: int) -> None:
    total_orders_canceled.inc(val)


def track_base_position(val: float) -> None:
    current_position_base.set(val)


def track_quote_position(val: float) -> None:
    current_position_quote.set(val)


def track_position(position: PositionInfo) -> None:
    track_base_position(float(position.total_base))
    track_quote_position(float(position.total_quote))

def track_current_spread(val: float) -> None:
    current_spread.set(val)

def track_current_fp(val: float) -> None:
    current_fp.set(val)

def track_current_best_ask_price(val: float) -> None:
    current_best_ask_price.set(val)

def track_current_best_bid_price(val: float) -> None:
    current_best_bid_price.set(val)

def track_current_best_ask_amount(val: float) -> None:
    current_best_ask_amount.set(val)

def track_current_best_bid_amount(val: float) -> None:
    current_best_bid_amount.set(val)

def track_quoted_info(orders: ReconciledOrders, fair_price: Decimal) -> None:
    orders_in_market = orders.to_keep + orders.to_place
    bids = [
        o for o in orders_in_market
        if o.order_side.lower() == 'bid'
    ]
    asks = [
        o for o in orders_in_market
        if o.order_side.lower() == 'ask'
    ]

    best_bid_price: float | None = None
    best_ask_price: float | None = None

    if bids:
        best_bid = max(bids, key = lambda x: x.price)
        best_bid_price = float(best_bid.price)
        track_current_best_bid_price(best_bid_price)
        track_current_best_bid_amount(float(best_bid.amount))

    if asks:
        best_ask = min(asks, key = lambda x: x.price)
        best_ask_price = float(best_ask.price)
        track_current_best_ask_price(best_ask_price)
        track_current_best_ask_amount(float(best_ask.amount))
       
    if best_bid_price and best_ask_price:
        track_current_spread(best_ask_price - best_bid_price)

    track_current_fp(float(fair_price))
