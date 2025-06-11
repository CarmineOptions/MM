from prometheus_client import Counter, Gauge, start_http_server
import logging
import time


def start_metrics_server(port: int = 8000) -> None:
    start_http_server(port)


last_error_gauge = Gauge(
    "last_error_timestamp", "Timestamp (in seconds) of the last error that occurred"
)

loop_time = Gauge(
    "loop_time", "Time (in seconds) it took the bot to complete one single loop"
)

total_orders_sent = Counter("total_orders_sent", "Total number of orders sent")

total_orders_canceled = Counter(
    "total_orders_canceled", "Total amount of orders that was sent"
)

current_position_base = Gauge(
    "current_position_base", "Current position in base token"
)
current_position_quote = Gauge(
    "current_position_quote", "Current position in quote token"
)

class PrometheusMetricsErrorHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            last_error_gauge.set(int(time.time()))


def track_loop_time(interval: float) -> None:
    loop_time.set(interval)


def track_orders_sent(val: int) -> None:
    total_orders_sent.inc(val)

def track_orders_canceled(val: int) -> None:
    total_orders_canceled.inc(val)

def track_base_position(val: float) -> None:
    current_position_base.set(val)

def track_quote_position(val: float) -> None:
    current_position_quote.set(val)
