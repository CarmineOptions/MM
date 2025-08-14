import os
from pydantic import BaseModel


class StarknetAccountConfig(BaseModel):
    '''
    Holds the configuration for the trading account.
    '''
    rpc_url_env: str
    wallet_address_env: str
    password_path_env: str
    keystore_path_env: str

    @property
    def rpc_url(self) -> str | None:
        return os.environ.get(self.rpc_url_env)

    @property
    def wallet_address(self) -> str | None:
        return os.environ.get(self.wallet_address_env)

    @property
    def keystore_path(self) -> str | None:
        return os.environ.get(self.keystore_path_env)

    @property
    def password(self) -> str | None:
        path = os.environ.get(self.password_path_env)
        if path is None:
            return None

        with open(path, "r") as f:
            pwd = f.read().strip()

        return pwd
    

class StarknetTxBuilderConfig(BaseModel):
    '''
    Holds the configuration for the tx builder.
    '''
    name: str

class StarknetPlatformConfig(BaseModel):
    account: StarknetAccountConfig
    tx_builder: StarknetTxBuilderConfig