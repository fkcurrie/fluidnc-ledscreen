import websocket
import time
import configparser
import os
import re
from datetime import datetime
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

# Initialize logger
logger = setup_logging()

class LEDDisplay:
    def __init__(self, ip_address):
        print("Initializing LED Display...")
        self.width = 64
        self.height = 32
        self.ip_address = ip_address  # Store IP address
        
        try:
            # Initialize the LED matrix
            self.geometry = Geometry(
                width=self.width, 
                height=self.height,
                n_addr_lines=4,
                rotation=Orientation.Normal
            )
            
            # Create two buffers for double buffering
            self.image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            self.draw = ImageDraw.Draw(self.image)
            
            # Initialize framebuffer and matrix
            self.framebuffer = np.asarray(self.image) + 0
            self.matrix = PioMatter(
                colorspace=Colorspace.RGB888Packed,
                pinout=Pinout.AdafruitMatrixBonnet,
                framebuffer=self.framebuffer,
                geometry=self.geometry
            )
            
            # Store previous state to prevent unnecessary updates
            self.prev_state = None
            self.prev_positions = None
            
            self.font = ImageFont.load_default()
            print("LED Display initialized successfully")
            
            self.test_display()
            
        except Exception as e:
            print(f"Error initializing LED Display: {e}")
            raise

    def test_display(self):
        """Display a test pattern to verify the display is working"""
        print("Running display test...")
        try:
            # Clear display
            self.clear_display()
            
            # Draw test shapes from working test script
            self.draw.rectangle((2, 2, 10, 10), fill=(0, 136, 0))     # Green square
            self.draw.ellipse((14, 2, 22, 10), fill=(136, 0, 0))      # Red circle
            self.draw.polygon([(28, 2), (32, 10), (24, 10)], fill=(0, 0, 136))  # Blue triangle
            
            # Update the display
            self.update_display()
            print("Test pattern displayed")
            time.sleep(2)  # Keep test pattern visible for 2 seconds
            
            # Now show the IP address
            self.clear_display()
            self.draw.text((2, 2), "FluidNC IP:", font=self.font, fill=(255, 255, 255))  # White text
            self.draw.text((2, 12), f"{self.ip_address}", font=self.font, fill=(255, 255, 0))  # Yellow text
            self.update_display()
            print(f"Displaying IP: {self.ip_address}")
            time.sleep(10)  # Show IP for 10 seconds
            
        except Exception as e:
            print(f"Display test failed: {e}")
            raise  # Re-raise the exception to catch initialization failures

    def clear_display(self):
        print("Clearing display...")
        self.draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))
        self.update_display()

    def display_position(self, status):
        try:
            # Check if state or position has changed
            current_state = status['state']
            current_positions = (
                status['position']['x'],
                status['position']['y'],
                status['position']['z']
            )
            
            if (self.prev_state == current_state and 
                self.prev_positions == current_positions):
                return  # Skip update if nothing changed
            
            # Create new image for this frame
            new_image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
            new_draw = ImageDraw.Draw(new_image)
            
            # Format and draw text
            state = f"{current_state}"
            x_pos = f"X:{current_positions[0]:.1f}"
            y_pos = f"Y:{current_positions[1]:.1f}"
            z_pos = f"Z:{current_positions[2]:.1f}"
            
            new_draw.text((2, 0), state, font=self.font, fill=(255, 255, 255))
            new_draw.text((2, 10), x_pos, font=self.font, fill=(255, 0, 0))
            new_draw.text((2, 20), y_pos, font=self.font, fill=(0, 255, 0))
            new_draw.text((32, 20), z_pos, font=self.font, fill=(0, 0, 255))
            new_draw.rectangle((0, 0, self.width-1, self.height-1), outline=(255, 255, 255))
            
            # Update framebuffer directly
            np.copyto(self.framebuffer, np.asarray(new_image))
            self.matrix.show()
            
            # Store current state
            self.prev_state = current_state
            self.prev_positions = current_positions
            
        except Exception as e:
            print(f"Error updating display: {e}")

    def update_display(self):
        try:
            np.copyto(self.framebuffer, np.asarray(self.image))
            self.matrix.show()  # Add explicit show() call
            print("Framebuffer updated")  # Debug output
        except Exception as e:
            print(f"Error in update_display: {e}")

def load_config():
    config = configparser.ConfigParser()
    
    # Define default values
    config['FluidNC'] = {
        'ip_address': '10.0.0.246',
        'update_interval': '0.05'
    }
    
    if os.path.exists('config'):
        config.read('config')
    else:
        with open('config', 'w') as configfile:
            config.write(configfile)
        print("Created new config file with default values")
    
    return config['FluidNC']

def parse_status_message(msg):
    # Convert bytes to string and remove b'' wrapper, \r\n etc
    msg = str(msg).strip("b'\\r\\n")
    
    # Parse using regex
    pattern = r'<(\w+)\|MPos:(-?\d+\.\d+),(-?\d+\.\d+),(-?\d+\.\d+)\|'
    match = re.search(pattern, msg)
    
    if match:
        state = match.group(1)
        x = float(match.group(2))
        y = float(match.group(3))
        z = float(match.group(4))
        return {
            'state': state,
            'position': {
                'x': x,
                'y': y,
                'z': z
            }
        }
    return None

def stream_status(ip_address, interval=0.2):
    print(f"Connecting to FluidNC WebSocket at {ip_address}...")
    ws_url = f"ws://{ip_address}:81"
    reconnect_count = 0
    
    # Initialize LED display once (this will run the test pattern)
    led_display = LEDDisplay(ip_address)
    
    while True:
        try:
            ws = websocket.WebSocket()
            ws.connect(ws_url)
            print("Connected! Press Ctrl+C to stop.")
            
            while True:
                ws.send("?".encode())
                
                msg = ws.recv()
                if "<" in str(msg):
                    status = parse_status_message(msg)
                    if status:
                        # Clear previous lines
                        print("\033[2J\033[H", end="")
                        
                        # Update terminal display
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        print(f"Time: {current_time}")
                        print(f"Machine State: {status['state']}")
                        print(f"Position:")
                        print(f"  X: {status['position']['x']:.3f} mm")
                        print(f"  Y: {status['position']['y']:.3f} mm")
                        print(f"  Z: {status['position']['z']:.3f} mm")
                        print(f"\nReconnections: {reconnect_count}")
                        print("Press Ctrl+C to stop")
                        
                        # Update LED display
                        led_display.display_position(status)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nStopping stream...")
            led_display.clear_display()
            break
        except Exception as e:
            print(f"\nConnection error: {e}")
            print("Attempting to reconnect...")
            reconnect_count += 1
            time.sleep(1)
        finally:
            try:
                ws.close()
            except:
                pass

def cleanup(signum, frame):
    print("\nCleaning up...")
    try:
        # Get access to the led_display instance from stream_status
        stream_status.led_display.clear_display()
    except:
        pass
    sys.exit(0)

def main():
    config = load_config()
    ip_address = config['ip_address']
    interval = float(config['update_interval'])
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    
    try:
        logger.info("Connecting to FluidNC WebSocket at %s...", ip_address)
        stream_status(ip_address, interval)
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 