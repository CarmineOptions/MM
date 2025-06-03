from prometheus_client import Counter, Gauge, Histogram, start_http_server
import logging
import time


def start_metrics_server(port: int = 8000):
    start_http_server(port)


last_error_gauge = Gauge(
    "last_error_timestamp",
    "Timestamp (in seconds) of the last error that occurred"
)

loop_time = Gauge(
    "loop_time",
    "Time (in seconds) it took the bot to complete one single loop"
)


class PrometheusMetricsErrorHandler(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            last_error_gauge.set(int(time.time()))


def track_loop_time(interval: float):
    loop_time.set(interval)

