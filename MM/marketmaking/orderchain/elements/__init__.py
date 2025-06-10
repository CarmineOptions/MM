from .fixed_params_element import FixedParamsElement
from ..order_chain import OrderChainElement


def get_element_from_name(name: str, **kwargs) -> OrderChainElement:
    if name == 'fixed_params':
        return FixedParamsElement(**kwargs)
    
    raise ValueError(f"Unknown OrderChainElement name `{name}`, kwargs: {kwargs}")