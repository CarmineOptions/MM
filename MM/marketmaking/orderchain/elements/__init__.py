
from typing import Any
from .element import OrderChainElement
from .fixed_params_element import FixedParamsElement

def get_element_from_name(name: str, **kwargs: Any) -> OrderChainElement:
    if name == 'fixed_params':
        return FixedParamsElement(**kwargs)
    
    raise ValueError(f"Unknown OrderChainElement name `{name}`, kwargs: {kwargs}")
