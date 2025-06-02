from typing import List
import asyncio
from starknet_py.net.websockets.websocket_client import WebsocketClient
from starknet_py.net.websockets.models import NewEventsNotification
from starknet_py.net.client_models import EmittedEvent



REMUS_ADDRESS = 0x067e7555f9ff00f5c4e9b353ad1f400e2274964ea0942483fae97363fd5d7958
RPC_URL = "ws://51.195.57.196:6060/"


async def main():
    # Initialize the WebsocketClient
    websocket_client = WebsocketClient(RPC_URL)
    await websocket_client.connect()

    emitted_events: List[EmittedEvent] = []
    def handler(new_events_notification: NewEventsNotification):
        nonlocal emitted_events
        emitted_events.append(new_events_notification.result)

    subscription_id = await websocket_client.subscribe_events(
        handler=handler,
        from_address=REMUS_ADDRESS
    )

    # # Subscribe to events and call MarketMaker.pulse on event
    # for event in emitted_events:
    #     print(f"Received event: {event}")
    #     # market_maker.pulse(event)


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
