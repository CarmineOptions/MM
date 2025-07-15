from typing import Any
from .element import OrderChainElement
from .fixed_params_element import FixedParamsElement
from .skew_fair_price_on_position_element import SkewFairPriceOnPositionElement
from .remove_orders_on_low_inventory_element import RemoveOrdersOnLowInventoryElement


def get_element_from_name(name: str, **kwargs: Any) -> OrderChainElement:
    if name == "fixed_params":
        return FixedParamsElement(**kwargs)

    if name == "skew_fair_price_on_position":
        return SkewFairPriceOnPositionElement(**kwargs)
    
    if name == 'remove_orders_on_low_inventory':
        return RemoveOrdersOnLowInventoryElement()

    raise ValueError(f"Unknown OrderChainElement name `{name}`, kwargs: {kwargs}")
