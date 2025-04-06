import websocket
import time
import configparser
import os
import re
# Restore LED imports
from adafruit_blinka_raspberry_pi5_piomatter import (
    PioMatter, 
    Geometry, 
    Orientation, 
    Colorspace,
    Pinout
)
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import signal
import sys
from logging_config import setup_logging
import threading
import socket
import logging
import ipaddress
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, IPVersion
from bdflib import reader

# Initialize logger
logger = setup_logging()

def load_config():
    """Load configuration from file"""
    config_path = os.path.join('config', 'fluidnc_config.ini') 
    defaults = {'hostname': 'fluidnc.local', 'ip_address': None} # Prioritize hostname
    try:
        config = configparser.ConfigParser()
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found at {config_path}, using defaults.")
            return defaults
        
        config.read(config_path)
        if 'FluidNC' not in config:
            logger.warning("Section [FluidNC] not found in config file, using defaults.")
            return defaults
        
        raw_config = dict(config['FluidNC'])
        
        return {
            'hostname': raw_config.get('hostname') or defaults['hostname'], # Use default if empty/missing
            'ip_address': raw_config.get('ip_address') # Allow static IP fallback
        }
    except Exception as e:
        logger.error(f"Error loading config: {e}, using defaults.")
        return defaults

def parse_status_message(msg):
    """Parse the FluidNC status message string (using flexible parser)."""
    try:
        # Decode if bytes and strip whitespace/control chars
        if isinstance(msg, bytes):
            msg_str = msg.decode('utf-8')
        else:
            msg_str = str(msg)
        
        msg_str = msg_str.strip('<>\r\n ')
        
        # Log all messages for debugging
        logger.debug(f"Processing message: {msg_str}")
        
        # Ignore non-status messages like PING or ID responses
        if not msg_str.startswith(('Idle', 'Run', 'Hold', 'Jog', 'Alarm', 'Door', 'Check', 'Home', 'Sleep')):
            logger.debug(f"Ignoring non-status message: {msg_str}")
            return None

        parts = msg_str.split('|')
        status_data = {'state': parts[0]} # First part is always the state
        logger.debug(f"Parsed state: {status_data['state']}")  # Debug log the state
        
        for part in parts[1:]:
            if ':' not in part:
                continue # Skip parts without a colon separator
                
            key, value = part.split(':', 1)
            logger.debug(f"Parsing part - key: {key}, value: {value}")  # Debug log each part
            
            if key == 'MPos':
                coords = value.split(',')
                if len(coords) == 3:
                    status_data['position'] = status_data.get('position', {})
                    status_data['position']['machine'] = {
                        'x': float(coords[0]),
                        'y': float(coords[1]),
                        'z': float(coords[2])
                    }
                    logger.debug(f"Parsed MPos: {status_data['position']['machine']}")  # Debug log position
            elif key == 'WPos': # Handle Work Position
                coords = value.split(',')
                if len(coords) == 3:
                    status_data['position'] = status_data.get('position', {})
                    status_data['position']['work'] = {
                        'x': float(coords[0]),
                        'y': float(coords[1]),
                        'z': float(coords[2])
                    }
            elif key == 'WCO': # Handle Work Coordinate Offset
                coords = value.split(',')
                if len(coords) == 3:
                    status_data['wco'] = {
                        'x': float(coords[0]),
                        'y': float(coords[1]),
                        'z': float(coords[2])
                    }
            elif key == 'FS': # Feed and Speed
                rates = value.split(',')
                if len(rates) == 2:
                    status_data['feed_rate'] = float(rates[0])
                    status_data['spindle_speed'] = float(rates[1])
            elif key == 'T': # Tool Number
                status_data['tool_number'] = int(value)
            elif key == 'S': # Spindle RPM
                status_data['spindle_rpm'] = float(value)
            else:
                status_data[key] = value # Store unknown fields
                
        # Check if we have at least the state and machine position
        if 'state' in status_data and 'machine' in status_data.get('position', {}):
            logger.debug(f"Successfully parsed status: {status_data}")  # Debug log successful parse
            return status_data
        else:
            logger.warning(f"Parsed status missing essential fields (state/mpos): {status_data} from message: {msg}")
            return None

    except Exception as e:
        logger.error(f"Error parsing status message '{msg}': {e}", exc_info=True)
        return None

class LEDDisplay:
    def __init__(self, matrix_width=64, matrix_height=32, brightness=0.5):
        """Initialize LED Display"""
        logger.info("Starting LED Display initialization...")
        self.width = matrix_width
        self.height = matrix_height
        self.is_connected = False # Add connection status flag
        self.connected_ip = "?.?.?.?" # Store the IP to display
        
        try:
            logger.debug("Creating geometry...")
            self.geometry = Geometry(
                width=self.width, 
                height=self.height,
                n_addr_lines=4,  # 16 pixels per panel, chain 2 panels vertically
                n_planes=8,  # Color depth
                n_temporal_planes=2,  # Temporal dithering
                rotation=Orientation.Normal
            )
            logger.debug("Geometry created.")
            
            logger.debug("Creating PIL image and drawing objects...")
            self.image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            self.draw = ImageDraw.Draw(self.image)
            logger.debug("PIL objects created.")
            
            logger.debug("Creating framebuffer...")
            self.framebuffer = np.asarray(self.image) + 0 # Mutable copy
            logger.debug("Framebuffer created.")

            logger.debug("Initializing PioMatter matrix...")
            self.matrix = PioMatter(
                colorspace=Colorspace.RGB888Packed,
                pinout=Pinout.AdafruitMatrixBonnet,
                framebuffer=self.framebuffer,
                geometry=self.geometry
            )
            logger.debug("PioMatter matrix initialized.")
            
            # --- Load Fonts --- 
            self.coord_font = None
            self.small_font = None 
            self.default_font = ImageFont.load_default() # Keep default as ultimate fallback
            self.bdf_font = None
            self.using_bdf = False

            # Try loading the BDF font for ALL text
            bdf_font_path = "/app/fonts/4x6.bdf"
            try:
                # First check if the fonts directory exists
                if not os.path.exists("/app/fonts"):
                    logger.warning("Fonts directory /app/fonts does not exist")
                    raise FileNotFoundError("Fonts directory not found")
                
                # Then check if the font file exists
                if not os.path.exists(bdf_font_path):
                    logger.warning(f"BDF Font file {bdf_font_path} does not exist")
                    raise FileNotFoundError(f"Font file not found: {bdf_font_path}")
                
                # Try to read the font file
                with open(bdf_font_path, "rb") as f:
                    self.bdf_font = reader.read_bdf(f)
                logger.info(f"Successfully loaded BDF font {bdf_font_path} using bdflib")
                # Use BDF for all fonts if loaded successfully
                self.coord_font = self.bdf_font # Assign to both
                self.small_font = self.bdf_font
                self.using_bdf = True
            except FileNotFoundError as e:
                logger.warning(f"BDF Font error: {e}, using default PIL font")
                self.coord_font = self.default_font
                self.small_font = self.default_font
            except Exception as e:
                logger.warning(f"Error loading BDF font {bdf_font_path} with bdflib: {e}, using default PIL font")
                self.coord_font = self.default_font
                self.small_font = self.default_font
             
            self.prev_state_str = None 
            
            logger.info("LED Display initialized successfully")
            self.show_startup_message("Connecting...") # Show initial message
            
        except Exception as e:
            logger.error(f"Error initializing LED Display: {e}", exc_info=True)
            raise # Reraise to prevent startup if display fails

    def set_connection_status(self, connected: bool, ip_address: str | None = None):
        """Update the connection status and store the IP."""
        if ip_address:
            self.connected_ip = ip_address
        elif not connected:
            self.connected_ip = "Disconnected" # Show text if disconnected
             
        if self.is_connected != connected:
            logger.info(f"Connection status changed to: {connected} (IP: {self.connected_ip})")
            self.is_connected = connected
            self.prev_state_str = None # Force redraw
            # Force a redraw next time display_status is called if only status changed

    def clear(self):
        """Clear the display buffer."""
        self.draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))

    def show(self):
        """Update the physical display with the current buffer contents."""
        try:
            np.copyto(self.framebuffer, np.asarray(self.image))
            self.matrix.show()
        except Exception as e:
            logger.error(f"Error showing on matrix: {e}", exc_info=True)

    def show_startup_message(self, message):
        self.clear()
        if self.using_bdf:
            # Calculate position for BDF rendering (may need adjustment)
            # bdflib doesn't have a textbbox equivalent easily
            # Approximate center based on character count and assumed width (4px for 4x6)
            approx_width = len(message) * 4
            text_x = (self.width - approx_width) // 2
            text_y = (self.height - 6) // 2 # Assumes 6px height
            self._draw_bdf_text((text_x, text_y), message, fill=(0, 150, 0)) # Green
        else:
            # Fallback to PIL default font drawing
            bbox = self.draw.textbbox((0, 0), message, font=self.default_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = (self.width - text_width) // 2
            text_y = (self.height - text_height) // 2
            self.draw.text((text_x, text_y), message, font=self.default_font, fill=(0, 150, 0))
        self._draw_connection_dot() 
        self._draw_ip_and_state("Starting...")
        self.show()

    def _draw_connection_dot(self):
        """Draws the connection status dot (blinking green if connected)."""
        if not self.is_connected:
            dot_color = (200, 0, 0) 
        else:
            # Change to 2-second interval by dividing time by 2
            if (int(time.time()) // 2) % 2 == 0: 
                dot_color = (0, 180, 0)
            else: 
                dot_color = (0, 0, 0) 
        
        x0 = 1  # Changed to top left
        y0 = 1
        x1 = 3
        y1 = 3
        # Draw directly onto self.draw (the buffer)
        self.draw.rectangle((x0, y0, x1, y1), fill=dot_color)

    def _draw_bdf_text(self, position, text, fill=(255, 255, 255)):
        """Helper to draw text using the loaded BDF font."""
        if not self.bdf_font or not self.using_bdf:
            # Fallback needed if BDF wasn't loaded or isn't being used
            self.draw.text(position, text, font=self.default_font, fill=fill)
            return

        x, y = position
        for char in text:
            try:
                glyph = self.bdf_font[ord(char)]
                # Get glyph data
                data = glyph.data  # This contains the actual bitmap data
                
                if data:
                    # Convert hex data to binary representation
                    binary_data = []
                    for byte in data:
                        # Convert each byte to binary and pad with zeros
                        binary = format(byte, '08b')
                        binary_data.append(binary)
                    
                    # Draw the bitmap (flipped vertically)
                    for row_idx, row in enumerate(reversed(binary_data)):  # Reverse the rows
                        target_y = y + row_idx
                        
                        for col_idx, bit in enumerate(row):
                            if bit == '1':
                                target_x = x + col_idx
                                if 0 <= target_x < self.width and 0 <= target_y < self.height:
                                    self.draw.point((target_x, target_y), fill=fill)
                
                # Move cursor for next character using fixed width
                x += 4  # Fixed width of 4 pixels for 4x6 font
                
            except Exception as e:
                logger.warning(f"Error rendering character '{char}' with BDF font: {e}")
                # Fall back to PIL font for this character
                self.draw.text((x, y), char, font=self.default_font, fill=fill)
                # Approximate advancement for mixed font rendering
                bbox = self.draw.textbbox((x, y), char, font=self.default_font)
                x += bbox[2] - bbox[0] + 1

    def _draw_ip_and_state(self, state_text):
        """Draw the IP address and state text."""
        logger.debug(f"Drawing IP ({self.connected_ip}) and state ({state_text})")
        self.clear()
        
        if self.using_bdf:
            # Draw IP address at top right
            ip_y = 1  # Top margin
            # Calculate IP position from right side
            ip_width = len(self.connected_ip) * 4  # Approximate width (4px per char)
            ip_x = self.width - ip_width - 6  # Leave room for dot
            self._draw_bdf_text((ip_x, ip_y), self.connected_ip, fill=(255, 255, 255))
            
            # Extract state and coordinates
            state_parts = state_text.split(' ')
            state = state_parts[0]  # The state (Idle, Run, etc)
            coords = state_parts[1:] if len(state_parts) > 1 else []  # The coordinates if present
            
            # Draw coordinates vertically on the left with normal font size
            if coords:
                coord_y = 6  # Start below IP
                coord_x = 1  # Left align
                
                # Define colors for each axis
                colors = {
                    'X': (255, 50, 50),    # Red for X
                    'Y': (50, 255, 50),    # Green for Y
                    'Z': (50, 50, 255)     # Blue for Z
                }
                
                # Process each coordinate
                for coord in coords:
                    axis = coord[0]  # Get the axis letter (X, Y, or Z)
                    value = coord[1:]  # Get the value
                    color = colors.get(axis, (255, 255, 255))  # Get color or default to white
                    
                    # Draw the entire coordinate (axis + value) at once
                    self._draw_bdf_text((coord_x, coord_y), coord, fill=color)
                    
                    # Move to next line
                    coord_y += 7  # Normal spacing between coordinates
                
                # Draw state on the same line as Z coordinate, aligned to right
                state_y = coord_y - 7  # Same line as last coordinate
                state_width = len(state) * 4  # Approximate width (4px per char)
                state_x = self.width - state_width - 6  # Right align, leave room for dot
                self._draw_bdf_text((state_x, state_y), state, fill=(255, 255, 255))
        else:
            # Fallback to PIL font with similar layout
            ip_y = 1
            # Draw IP on right
            bbox = self.draw.textbbox((0, 0), self.connected_ip, font=self.default_font)
            ip_width = bbox[2] - bbox[0]
            ip_x = self.width - ip_width - 6
            self.draw.text((ip_x, ip_y), self.connected_ip, font=self.default_font, fill=(255, 255, 255))
            
            # Get IP text height
            ip_height = bbox[3] - bbox[1]
            
            # Split state and coordinates
            state_parts = state_text.split(' ')
            state = state_parts[0]
            coords = state_parts[1:] if len(state_parts) > 1 else []
            
            # Draw coordinates vertically on left with normal font size
            if coords:
                coord_y = ip_y + ip_height + 1
                coord_x = 1
                colors = {
                    'X': (255, 50, 50),
                    'Y': (50, 255, 50),
                    'Z': (50, 50, 255)
                }
                
                for coord in coords:
                    axis = coord[0]
                    color = colors.get(axis, (255, 255, 255))
                    self.draw.text((coord_x, coord_y), coord, font=self.default_font, fill=color)
                    coord_y += ip_height + 1
                
                # Draw state on the same line as Z coordinate, aligned to right
                state_y = coord_y - (ip_height + 1)  # Same line as last coordinate
                bbox = self.draw.textbbox((0, 0), state, font=self.default_font)
                state_width = bbox[2] - bbox[0]
                state_x = self.width - state_width - 6  # Right align, leave room for dot
                self.draw.text((state_x, state_y), state, font=self.default_font, fill=(255, 255, 255))
        
        # Draw connection dot last so it's always visible
        self._draw_connection_dot()
        logger.debug("Display buffer updated with new IP and state")

    def update_display_buffer(self, status_data):
        """Update the display buffer with new status data."""
        if not status_data:
            logger.debug("No status data to update display with")
            return
            
        # Format state string
        state_str = status_data['state']
        if 'position' in status_data and 'machine' in status_data['position']:
            pos = status_data['position']['machine']
            state_str = f"{state_str} X{pos['x']:.1f} Y{pos['y']:.1f} Z{pos['z']:.1f}"
            logger.debug(f"Formatted state string: {state_str}")
            
        # Always update display for any status change
        logger.debug(f"Updating display with state: {state_str}")
        self._draw_ip_and_state(state_str)
        self.prev_state_str = state_str
        self.show()  # Force immediate display update

    def refresh_display(self):
        """Force a refresh of the physical display."""
        self.show()

    def cleanup(self):
        """Clean up resources."""
        try:
            self.clear()
            self.show()
        except Exception as e:
            logger.error(f"Error during display cleanup: {e}")

class FluidNCListener(ServiceListener):
    """Zeroconf listener to find FluidNC WebSocket service."""
    def __init__(self):
        self.found_services = {}
        self.lock = threading.Lock()

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        logger.info(f"Service {name} removed")
        with self.lock:
            if name in self.found_services:
                del self.found_services[name]

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            # --- MODIFIED IP ADDRESS HANDLING --- 
            ipv4_addresses = []
            try:
                # Iterate through parsed addresses and check family
                for ip_bytes in info.addresses:
                    # Attempt to determine address family (might need more robust check)
                    # This assumes standard IPv4 length (4 bytes)
                    if len(ip_bytes) == 4: # Likely IPv4
                        ipv4_addresses.append(socket.inet_ntoa(ip_bytes))
            except Exception as e:
                logger.warning(f"Error processing addresses for service {name}: {e}")
            # --- END MODIFICATION --- 

            logger.info(f"Service {name} added, type: {type_}, ipv4 addresses: {ipv4_addresses}, port: {info.port}")
            # Store relevant info - assuming port 81 for WebSocket
            if info.port == 80 and ipv4_addresses: # Find the HTTP service (WS is usually HTTP port + 1)
                with self.lock:
                    # Store the first IPv4 address found for port 80
                    self.found_services[name] = ipv4_addresses[0] 
                    logger.info(f"Found potential FluidNC HTTP service '{name}' at {ipv4_addresses[0]}:80. Will try WebSocket on port 81.")

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        # Less common, but handle same as add for simplicity
        self.add_service(zc, type_, name)

    def get_fluidnc_ip(self, preferred_name="fluidnc.local.") -> str | None:
        """Get the IP address ONLY if the preferred service name is found."""
        with self.lock:
            # Only return if the exact preferred name is found
            if preferred_name in self.found_services:
                logger.info(f"Preferred service '{preferred_name}' found, returning IP: {self.found_services[preferred_name]}")
                return self.found_services[preferred_name]
            else:
                logger.warning(f"Preferred service '{preferred_name}' not found in discovered services: {list(self.found_services.keys())}")
                return None # Do not fall back to other services

def discover_fluidnc_zeroconf(timeout=10) -> str | None:
    """Discover FluidNC using Zeroconf/mDNS."""
    logger.info(f"Starting Zeroconf discovery for _http._tcp.local. (timeout={timeout}s)")
    ip_address = None
    zeroconf = None
    try:
        zeroconf = Zeroconf()
        listener = FluidNCListener()
        # Browse for HTTP services, as WebSocket is often not advertised directly
        browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
        
        # Wait for discovery
        time.sleep(timeout) 
        
        # Check results - construct preferred name from config/default
        config_hostname = load_config().get('hostname', 'fluidnc.local')
        preferred_zeroconf_name = f"{config_hostname.rstrip('.')}._http._tcp.local."
        ip_address = listener.get_fluidnc_ip(preferred_name=preferred_zeroconf_name)
        
        if ip_address:
            logger.info(f"Zeroconf discovered FluidNC IP: {ip_address}")
        else:
            logger.warning("Zeroconf discovery did not find a suitable FluidNC service.")
             
    except Exception as e:
        logger.error(f"Zeroconf discovery failed: {e}")
    finally:
        if zeroconf:
            zeroconf.close()
            logger.info("Zeroconf closed.")
            
    return ip_address

def connect_websocket(target_host_or_ip, max_retries=3, retry_delay=5):
    """Connect to the WebSocket server with retry logic."""
    logger.debug(f"connect_websocket called with target: {target_host_or_ip}")
    
    # Directly use the provided target (should be an IP from discovery or config)
    ip_to_use = None
    try:
        ipaddress.ip_address(target_host_or_ip)
        ip_to_use = target_host_or_ip
    except ValueError:
        logger.error(f"connect_websocket called with non-IP: {target_host_or_ip}. This shouldn't happen after discovery/config check.")
        return None
        
    if not ip_to_use:
        logger.error("No valid IP address found for WebSocket connection.")
        return None
        
    ws_url = f"ws://{ip_to_use}:81/ws"
    logger.info(f"Attempting WebSocket connection to {ws_url}")
    
    for attempt in range(max_retries):
        try:
            # Create WebSocket connection
            ws = websocket.WebSocket()
            ws.connect(ws_url)
            logger.info(f"Successfully connected to WebSocket at {ws_url}")
            
            # Request status messages
            ws.send("?")  # Send a single ? to request status
            logger.debug("Sent status request message")
            
            return ws
        except Exception as e:
            logger.error(f"WebSocket connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:  # Don't sleep after last attempt
                time.sleep(retry_delay)
    
    logger.error(f"Failed to connect to WebSocket after {max_retries} attempts")
    return None

def keep_alive(ws):
    """Send periodic ping to keep the connection alive."""
    try:
        ws.ping()
    except Exception as e:
        logger.error(f"Error sending ping: {e}")
        raise  # Re-raise to trigger reconnection

def main():
    """Main function."""
    display = None
    ws = None
    last_ping = 0
    last_status_request = 0
    ping_interval = 5  # seconds
    status_request_interval = 0.5  # Request status every 0.5 seconds
    
    try:
        # Initialize display first
        display = LEDDisplay()
        
        while True:  # Main connection loop
            try:
                # Load configuration
                config = load_config()
                
                # Try to get IP address
                ip_address = None
                
                # First try static IP if configured
                if config.get('ip_address'):
                    try:
                        # Validate static IP
                        ipaddress.ip_address(config['ip_address'])
                        ip_address = config['ip_address']
                        logger.info(f"Using static IP from config: {ip_address}")
                    except ValueError:
                        logger.warning(f"Invalid static IP in config: {config['ip_address']}")
                
                # Fall back to Zeroconf discovery if no static IP or invalid
                if not ip_address:
                    logger.info("No valid static IP, attempting Zeroconf discovery...")
                    ip_address = discover_fluidnc_zeroconf()
                
                if not ip_address:
                    logger.error("Failed to obtain IP address")
                    display.set_connection_status(False)
                    time.sleep(5)  # Wait before retry
                    continue
                
                # Try to connect WebSocket
                ws = connect_websocket(ip_address)
                if not ws:
                    logger.error("Failed to establish WebSocket connection")
                    display.set_connection_status(False)
                    time.sleep(5)  # Wait before retry
                    continue
                
                # Connection successful
                display.set_connection_status(True, ip_address)
                display._draw_ip_and_state("Connected")  # Show connected state immediately
                display.show()
                
                # Main message loop
                while True:
                    current_time = time.time()
                    
                    # Handle keep-alive
                    if current_time - last_ping >= ping_interval:
                        keep_alive(ws)
                        last_ping = current_time
                    
                    # Request status updates more frequently
                    if current_time - last_status_request >= status_request_interval:
                        try:
                            ws.send("?")  # Request status update
                            last_status_request = current_time
                            logger.debug("Sent status request")
                        except Exception as e:
                            logger.error(f"Error sending status request: {e}")
                            break
                    
                    # Check for messages with shorter timeout for more responsive updates
                    try:
                        ws.settimeout(0.1)  # Reduced timeout for more responsive updates
                        message = ws.recv()
                        logger.debug(f"Received WebSocket message: {message}")
                        
                        # Parse and update display
                        status = parse_status_message(message)
                        if status:
                            # Force a display refresh before updating
                            display.show()
                            display.update_display_buffer(status)
                            # Force another display refresh after updating
                            display.show()
                        else:
                            logger.debug(f"Message not parsed as status: {message}")
                            
                    except websocket.WebSocketTimeoutException:
                        continue  # Normal timeout, just continue
                    except Exception as e:
                        logger.error(f"Error in message loop: {e}")
                        break  # Break inner loop to trigger reconnection
                        
            except Exception as e:
                logger.error(f"Error in connection loop: {e}")
                if ws:
                    try:
                        ws.close()
                    except:
                        pass
                    ws = None
                display.set_connection_status(False)
                time.sleep(5)  # Wait before retry
                
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        if ws:
            try:
                ws.close()
            except:
                pass
        if display:
            display.cleanup()

def cleanup(signum, frame):
    """Signal handler for cleanup."""
    logger.info(f"Received signal {signum}, initiating cleanup...")
    sys.exit(0)  # This will trigger the finally block in main()

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    
    main() 