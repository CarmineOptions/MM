from decimal import Decimal
from .order_reconciler import OrderReconciler
from .bounded_reconciler import BoundedReconciler
from .always_replace_reconciler import AlwaysReplaceOrderReconciler
from .tolerance_reconciler import ToleranceOrderReconciler

from cfg.cfg_classes import ReconcilerConfig


def get_reconciler(cfg: ReconcilerConfig) -> OrderReconciler:
    if cfg.name == "bounded_reconciler":
        return BoundedReconciler(
            max_relative_distance_from_fp=Decimal(
                cfg.args["max_relative_distance_from_fp"]
            ),
            min_relative_distnace_from_fp=Decimal(
                cfg.args["min_relative_distance_from_fp"]
            ),
            minimal_remaining_size=Decimal(cfg.args["minimal_remaining_size"]),
            max_orders_per_side=int(cfg.args["max_orders_per_side"]),
        )
    if cfg.name == "always_replace_reconciler":
        return AlwaysReplaceOrderReconciler()
    
    if cfg.name == "tolerance_reconciler":
        return ToleranceOrderReconciler(
            relative_price_tolerance=Decimal(cfg.args["relative_price_tolerance"]),
            relative_quantity_tolerance=Decimal(cfg.args["relative_quantity_tolerance"]),
        )

    raise ValueError(f"Unknown OrderReconciler name: {cfg.name}")
