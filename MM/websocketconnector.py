import websockets
import json
import logging


class WebSocketConnector:
    def __init__(self, rpc_url: str) -> None:
        """
        Initializes the WebSocketConnector.

        :param rpc_url: The WebSocket URL for the Starknet RPC endpoint.
        """
        self.rpc_url = rpc_url
        self.connection = None
        self._logger = logging.getLogger(self.__class__.__name__)
        handler = logging.FileHandler("websocket_connector.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    async def connect(self) -> None:
        """
        Establishes a WebSocket connection to the Starknet RPC endpoint.
        """
        try:
            self._logger.info(f"Connecting to {self.rpc_url}...")
            self.connection = await websockets.connect(self.rpc_url)
            self._logger.info("WebSocket connection established.")
        except Exception as e:
            self._logger.error(f"Failed to connect to {self.rpc_url}: {e}")
            raise

    async def send(self, message: dict) -> None:
        """
        Sends a message to the WebSocket server.

        :param message: The message to send, as a dictionary.
        """
        if not self.connection:
            raise ConnectionError("WebSocket is not connected.")
        try:
            await self.connection.send(json.dumps(message))
            self._logger.info(f"Message sent: {message}")
        except Exception as e:
            self._logger.error(f"Failed to send message: {e}")
            raise

    async def receive(self) -> dict:
        """
        Receives a message from the WebSocket server.

        :return: The received message as a dictionary.
        """
        if not self.connection:
            raise ConnectionError("WebSocket is not connected.")
        try:
            response = await self.connection.recv()
            self._logger.info(f"Message received: {response}")
            return json.loads(response)
        except Exception as e:
            self._logger.error(f"Failed to receive message: {e}")
            raise

    async def close(self) -> None:
        """
        Closes the WebSocket connection.
        """
        if self.connection:
            try:
                await self.connection.close()
                self._logger.info("WebSocket connection closed.")
            except Exception as e:
                self._logger.error(f"Failed to close WebSocket connection: {e}")
                raise
