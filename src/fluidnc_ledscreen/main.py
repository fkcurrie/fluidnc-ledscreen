"""Main entry point for FluidNC LED Screen Monitor.

This module provides the main entry point for the FluidNC LED Screen Monitor
application, handling initialization and coordination of components.
"""

import asyncio
import logging
import signal
from typing import Optional

from fluidnc_ledscreen.led_screen import LEDScreen
from fluidnc_ledscreen.websocket_client import WebSocketClient

logger = logging.getLogger(__name__)


class FluidNCLEDScreen:
    """Main application class for FluidNC LED Screen Monitor.

    This class coordinates the WebSocket client and LED screen display,
    handling the main application loop and shutdown.
    """

    def __init__(
        self,
        websocket_url: str,
        led_count: int = 60,
        led_pin: int = 18,
        led_brightness: int = 255,
    ) -> None:
        """Initialize the FluidNC LED Screen Monitor.

        Args:
            websocket_url: WebSocket URL for FluidNC connection
            led_count: Number of LEDs in the strip
            led_pin: GPIO pin for LED control
            led_brightness: LED brightness (0-255)
        """
        self.websocket_client = WebSocketClient(
            url=websocket_url,
            message_callback=self._handle_message,
        )
        self.led_screen = LEDScreen()
        self.running = False
        self._shutdown_event: Optional[asyncio.Event] = None

    async def start(self) -> None:
        """Start the application."""
        try:
            self.running = True
            self._shutdown_event = asyncio.Event()

            # Set up signal handlers
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop = asyncio.get_event_loop()
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self._handle_signal(s)),
                )

            # Start WebSocket client
            await self.websocket_client.connect()

            # Wait for shutdown
            await self._shutdown_event.wait()
        except (asyncio.CancelledError, KeyboardInterrupt) as e:
            logger.info("Application shutdown requested: %s", str(e))
        except asyncio.TimeoutError as e:
            logger.error("Application timeout: %s", str(e))
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the application."""
        self.running = False
        await self.websocket_client.disconnect()
        self.led_screen.cleanup()

    async def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signals.

        Args:
            sig: Signal received
        """
        logger.info("Received signal %s, shutting down", sig.name)
        if self._shutdown_event:
            self._shutdown_event.set()

    def _handle_message(self, message: dict) -> None:
        """Handle messages from FluidNC.

        Args:
            message: Message data from FluidNC
        """
        try:
            self.led_screen.update(message)
        except (KeyError, ValueError) as e:
            logger.error("Invalid message format: %s", str(e))
        except RuntimeError as e:
            logger.error("LED screen error: %s", str(e))


def main() -> None:
    """Run the FluidNC LED Screen Monitor application.

    Sets up logging configuration and starts the main application loop.
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and run application
    app = FluidNCLEDScreen(websocket_url="ws://localhost:81")
    asyncio.run(app.start())


if __name__ == "__main__":
    main()
