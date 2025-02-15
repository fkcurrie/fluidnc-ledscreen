# FluidNC Position Monitor

A simple Python script to monitor the position and state of a FluidNC CNC machine using WebSocket communication.

## Requirements

- Python 3.x
- WebSocket client library
- FluidNC-enabled CNC machine

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/fkcurrie/fluidnc-ledscreen.git
   cd fluidnc-ledscreen
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit the `config` file to set your FluidNC machine's IP address and update interval:
   ```ini
   [FluidNC]
   ip_address = <your-fluidnc-ip>
   update_interval = 0.2  # Updates every 200ms
   ```

## Running the Script

1. Activate the virtual environment:
   ```bash
   source fluidnc-ledscreen/bin/activate
   ```

2. Run the script (LED matrix requires sudo):
   ```bash
   sudo -E env PATH=$PATH python3 fluidnc_monitor.py
   ```

Note: The script requires sudo privileges to access the LED matrix hardware, but must preserve the Python virtual environment.

The script will:
- Connect to your FluidNC machine via WebSocket
- Display real-time position (X, Y, Z) and machine state on both terminal and LED matrix
- Show timestamp for each update
- Automatically reconnect if connection is lost
- Display reconnection count

Press Ctrl+C to stop the monitor.

## Output Example
   ```
   Time: 2024-02-15 14:12:15.739
   Machine State: Idle
   Position:
     X: 0.000 mm
     Y: 0.000 mm
     Z: 0.000 mm

   Reconnections: 0
   Press Ctrl+C to stop
   ``` 