import typing
from abc import ABC, abstractmethod


if typing.TYPE_CHECKING:
    from cfg.cfg_classes import StrategyConfig
    from marketmaking.reconciling.order_reconciler import ReconciledOrders
    from markets.market import PrologueOps
    from state.state import State


class PlatformABC(ABC):
    @staticmethod
    @abstractmethod
    async def from_config(cfg: StrategyConfig) -> "PlatformABC":
        '''
        Create a Platform instance from config
        '''
        raise NotImplementedError

    @abstractmethod
    async def initialize_trading(self) -> None:
        raise NotImplementedError
    
    @abstractmethod
    async def execute_operations(self, state: "State", prologue: "list[PrologueOps]", ops: ReconciledOrders) -> None:
        raise NotImplementedError
    
    @abstractmethod
    async def error_handled(self, e: Exception) -> bool:
        raise NotImplementedError