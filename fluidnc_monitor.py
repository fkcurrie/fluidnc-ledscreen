"""FluidNC Monitor Module.

This module provides functionality to monitor FluidNC controllers on the
network and manage their connections.
"""

import asyncio
import json
import logging
from typing import Optional

import websockets
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf

logger = logging.getLogger(__name__)


class FluidNCMonitor:
    """Monitor for FluidNC controllers on the network.

    This class handles discovery and monitoring of FluidNC controllers
    using Zeroconf/mDNS.
    """

    def __init__(
        self,
        on_controller_found: Optional[callable] = None,
        on_controller_lost: Optional[callable] = None,
    ) -> None:
        """Initialize the FluidNC monitor.

        Args:
            on_controller_found: Callback when a controller is found
            on_controller_lost: Callback when a controller is lost
        """
        self.zeroconf = Zeroconf()
        service_type = "_fluidnc._tcp.local."
        self.browser = ServiceBrowser(
            zeroconf=self.zeroconf,
            type_=service_type,
            handler=self,
        )
        self.controllers = {}
        self.on_controller_found = on_controller_found
        self.on_controller_lost = on_controller_lost

    def remove_service(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
    ) -> None:
        """Handle service removal.

        Args:
            zeroconf: Zeroconf instance
            service_type: Type of service
            name: Name of service
        """
        if name in self.controllers:
            controller = self.controllers.pop(name)
            if self.on_controller_lost:
                self.on_controller_lost(controller)

    def add_service(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
    ) -> None:
        """Handle service addition.

        Args:
            zeroconf: Zeroconf instance
            service_type: Type of service
            name: Name of service
        """
        info = zeroconf.get_service_info(service_type, name)
        if info:
            self.controllers[name] = info
            if self.on_controller_found:
                self.on_controller_found(info)

    def get_controllers(self) -> list[ServiceInfo]:
        """Get list of discovered controllers.

        Returns:
            List of discovered FluidNC controllers
        """
        return list(self.controllers.values())

    def close(self) -> None:
        """Close the monitor and cleanup resources."""
        self.zeroconf.close()


class FluidNCClient:
    """Client for communicating with FluidNC controllers.

    This class handles WebSocket communication with FluidNC controllers.
    """

    def __init__(
        self,
        host: str,
        port: int = 81,
        on_message: Optional[callable] = None,
    ) -> None:
        """Initialize the FluidNC client.

        Args:
            host: Host address of the controller
            port: Port number (default: 81)
            on_message: Callback for received messages
        """
        self.host = host
        self.port = port
        self.on_message = on_message
        self.websocket = None
        self.running = False

    async def connect(self) -> None:
        """Establish connection to the controller."""
        try:
            uri = f"ws://{self.host}:{self.port}/ws"
            self.websocket = await websockets.connect(uri)
            self.running = True
            asyncio.create_task(self._handle_messages())
        except Exception as e:
            logger.error("Failed to connect to FluidNC: %s", str(e))
            self.running = False
            raise

    async def disconnect(self) -> None:
        """Close connection to the controller."""
        self.running = False
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error("Error closing connection: %s", str(e))
            finally:
                self.websocket = None

    async def _handle_messages(self) -> None:
        """Handle incoming WebSocket messages."""
        while self.running and self.websocket:
            try:
                message = await self.websocket.recv()
                if self.on_message:
                    self.on_message(json.loads(message))
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                await self.disconnect()
            except Exception as e:
                logger.error("Error handling message: %s", str(e))
                await self.disconnect()

    async def send_message(self, message: dict) -> None:
        """Send message to the controller.

        Args:
            message: Message to send
        """
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                logger.error("Error sending message: %s", str(e))
                await self.disconnect()


async def main() -> None:
    """Run the monitor until interrupted."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    def log_controller_found(info):
        """Log when a controller is found."""
        logger.info("Found controller: %s", info.name)

    def log_controller_lost(info):
        """Log when a controller is lost."""
        logger.info("Lost controller: %s", info.name)

    # Create monitor with callbacks
    monitor = FluidNCMonitor(
        on_controller_found=log_controller_found,
        on_controller_lost=log_controller_lost,
    )

    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        monitor.close()


if __name__ == "__main__":
    asyncio.run(main())
