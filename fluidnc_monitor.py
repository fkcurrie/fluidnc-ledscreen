import websocket
import time
import configparser
import os
import re
from datetime import datetime

def load_config():
    config = configparser.ConfigParser()
    
    # Define default values
    config['FluidNC'] = {
        'ip_address': '10.0.0.246',
        'update_interval': '0.2'
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
    
    while True:
        try:
            # Connect to WebSocket
            ws = websocket.WebSocket()
            ws.connect(ws_url)
            print("Connected! Press Ctrl+C to stop.")
            
            while True:
                # Send status request
                ws.send("?".encode())
                
                # Get and parse status
                msg = ws.recv()
                if "<" in str(msg):
                    status = parse_status_message(msg)
                    if status:
                        # Clear previous lines
                        print("\033[2J\033[H", end="")  # Clear screen and move to top
                        
                        # Add timestamp with milliseconds
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        print(f"Time: {current_time}")
                        print(f"Machine State: {status['state']}")
                        print(f"Position:")
                        print(f"  X: {status['position']['x']:.3f} mm")
                        print(f"  Y: {status['position']['y']:.3f} mm")
                        print(f"  Z: {status['position']['z']:.3f} mm")
                        print(f"\nReconnections: {reconnect_count}")
                        print("Press Ctrl+C to stop")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nStopping stream...")
            break
        except Exception as e:
            print(f"\nConnection error: {e}")
            print("Attempting to reconnect...")
            reconnect_count += 1
            time.sleep(1)  # Wait a second before reconnecting
        finally:
            try:
                ws.close()
            except:
                pass

def main():
    config = load_config()
    ip_address = config['ip_address']
    interval = float(config['update_interval'])
    
    try:
        stream_status(ip_address, interval)
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 