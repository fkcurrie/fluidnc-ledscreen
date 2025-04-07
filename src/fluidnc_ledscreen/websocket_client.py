"""WebSocket client for FluidNC communication.

This module handles WebSocket communication with the FluidNC controller,
managing connection, message handling, and reconnection logic.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

import websockets
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionError,
    InvalidStatusCode,
    WebSocketException,
)

logger = logging.getLogger(__name__)

# Type aliases
MessageCallback = Callable[[Dict[str, Any]], None]
WSProtocol = websockets.WebSocketClientProtocol


class WebSocketClient:
    """WebSocket client for FluidNC communication.

    This class manages the WebSocket connection to FluidNC, handling
    connection, message processing, and automatic reconnection.

    Attributes:
        url: WebSocket URL to connect to
        reconnect_interval: Time between reconnection attempts
        message_callback: Callback function for received messages
    """

    def __init__(
        self,
        url: str,
        reconnect_interval: float = 5.0,
        message_callback: Optional[MessageCallback] = None,
    ) -> None:
        """Initialize the WebSocket client.

        Args:
            url: WebSocket URL to connect to
            reconnect_interval: Time between reconnection attempts
            message_callback: Callback function for received messages
        """
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.message_callback = message_callback
        self.websocket: Optional[WSProtocol] = None
        self.running = False
        self._connection_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Establish WebSocket connection."""
        try:
            self.websocket = await websockets.connect(self.url)
            logger.info("Connected to FluidNC WebSocket")
            self.running = True
            self._connection_task = asyncio.create_task(self._handle_messages())
        except (ConnectionError, InvalidStatusCode) as e:
            logger.error("Failed to connect to FluidNC: %s", str(e))
            self.running = False
            raise

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        self.running = False
        if self.websocket:
            try:
                await self.websocket.close()
            except WebSocketException as e:
                logger.error("Error closing connection: %s", str(e))
            finally:
                self.websocket = None
        if self._connection_task:
            self._connection_task.cancel()
            self._connection_task = None

    async def _handle_messages(self) -> None:
        """Handle incoming WebSocket messages."""
        while self.running and self.websocket:
            try:
                msg = await self.websocket.recv()
                await self._process_message(msg)
            except ConnectionClosed:
                logger.warning("WebSocket connection closed")
                await self._reconnect()
            except WebSocketException as e:
                logger.error("Error handling message: %s", str(e))
                await self._reconnect()

    async def _process_message(self, message: str) -> None:
        """Process received WebSocket message.

        Args:
            message: Raw message string from WebSocket
        """
        try:
            data = json.loads(message)
            if self.message_callback:
                self.message_callback(data)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse message: %s", str(e))

    async def _reconnect(self) -> None:
        """Attempt to reconnect to WebSocket."""
        if not self.running:
            return

        logger.info(
            "Attempting to reconnect in %s seconds",
            self.reconnect_interval,
        )
        await asyncio.sleep(self.reconnect_interval)
        try:
            await self.connect()
        except (ConnectionError, InvalidStatusCode) as e:
            logger.error("Reconnection failed: %s", str(e))
            self.running = False
