import asyncio
# from starknet_py.net.client_models import EventFilter
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.models.chains import StarknetChainId
# from starknet_py.net.models import Address
from starknet_py.net.websockets.websocket_client import WebsocketClient
from MM.marketmaking.marketmaker import MarketMaker, Market, WAccount, StateMarket, State
from starknet_py.net.websockets.models import NewEventsNotification

REMUS_ADDRESS = 0x067e7555f9ff00f5c4e9b353ad1f400e2274964ea0942483fae97363fd5d7958
# WebSocket URL for Starknet RPC
RPC_URL = "wss://starknet-mainnet.blastapi.io/f9761ebe-0782-403a-9272-7ead17dfffd5"

from starknet_py.net.client_models import (
    BlockHeader,
    Call,
    EmittedEvent,
    TransactionExecutionStatus,
    TransactionStatus,
)
from typing import List
from starknet_py.net.websockets.models import NewEventsNotification



def get_account() -> Account:
    """Get a market makers account."""
    client = FullNodeClient(node_url = env_config.starknet_rpc)
    account = Account(
        client = client,
        address = env_config.wallet_address,
        key_pair = KeyPair.from_keystore(env_config.path_to_keystore, env_config.account_password),
        chain = StarknetChainId[env_config.network]
    )
    logging.info("Succesfully loaded account.")
    return account


async def main():
    market = Market(
            market_id: str,
            dex_contract: TODO,
            base_token_contract: TODO,
            quote_token_contract: TODO,
            dex_address: str,
            base_token_address: str,
            quote_token_address: str,
    )
    account = get_account()
    wrapped_account = WAccount(account=account)

    state_market = StateMarket(accounts=[wrapped_account], market=market)

    state = State(markets=[market], accounts=[wrapped_account])

    poc_mm_model = POCMMModel(state_market=state_market)

    market_maker = MarketMaker(
        accounts=[wrapped_account],
        markets=[market],
        account_market_pairs={wrapped_account: [market]},
        state=state,
        mm_model=poc_mm_model,
        reconciler=None,
        claim_rule=None,
        transaction_builder=None,
        blockchain_connectors=None
    )


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())



#####################
# when wss is working
#####################

# async def main():

#     # Initialize the WebsocketClient
#     websocket_client = WebsocketClient(RPC_URL)
#     await websocket_client.connect()
#     print(f"Connected to {RPC_URL}")

#     # Define the event filter
#     # event_filter = EventFilter(
#     #     from_address=REMUS_ADDRESS,  # Replace with the contract address
#     #     keys=[]  # Replace with the event keys
#     # )

#     # Initialize the MarketMaker instance
#     # market_maker = MarketMaker(
#     #     accounts="TODO",
#     #     markets="TODO",
#     #     state="TODO",
#     #     chain="TODO",
#     #     reconciler="TODO",
#     #     claim_rule="TODO",
#     #     transaction_builder="TODO",
#     #     blockchain_connectors="TODO",
#     # )

#     emitted_events: List[EmittedEvent] = []
#     def handler(new_events_notification: NewEventsNotification):
#         emitted_events.append(new_events_notification.result)
    
#     subscription_id = await websocket_client.subscribe_events(
#         handler=handler,
#         from_address=REMUS_ADDRESS
#     )
#     # subscription_id = await websocket_client.subscribe_pending_transactions(
#     #     handler=print,
#     #     sender_address=[0x463de332da5b88a1676bfb4671dcbe4cc1a9147c46300a1658ed43a22d830c3]
#     # )



#     # Subscribe to events and call MarketMaker.pulse on event
#     for event in emitted_events:
#         print(f"Received event: {event}")
#         # market_maker.pulse(event)