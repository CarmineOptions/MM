from decimal import Decimal
from .order_reconciler import OrderReconciler
from .always_replace_reconciler import AlwaysReplaceOrderReconciler
from .tolerance_reconciler import ToleranceOrderReconciler

from cfg.cfg_classes import ReconcilerConfig


def get_reconciler(cfg: ReconcilerConfig) -> OrderReconciler:
    if cfg.name == "always_replace_reconciler":
        return AlwaysReplaceOrderReconciler()
    
    if cfg.name == "tolerance_reconciler":
        return ToleranceOrderReconciler(
            relative_price_tolerance=Decimal(cfg.args["relative_price_tolerance"]),
            relative_quantity_tolerance=Decimal(cfg.args["relative_quantity_tolerance"]),
        )

    raise ValueError(f"Unknown OrderReconciler name: {cfg.name}")
