
from abc import ABC, abstractmethod

from cfg.cfg_classes import StrategyConfig


class PlatformABC(ABC):
    @staticmethod
    @abstractmethod
    async def from_config(cfg: StrategyConfig) -> "PlatformABC":
        '''
        Create a Platform instance from config
        '''
        raise NotImplementedError


