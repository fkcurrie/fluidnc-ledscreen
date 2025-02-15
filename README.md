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

There are two ways to configure the application:

1. Using the config file:
   ```ini
   [FluidNC]
   ip_address = <your-fluidnc-ip>
   update_interval = 0.05  # Updates every 50ms
   ```

2. Using environment variables (for Docker):
   The application will automatically create a `.env` file based on your config file.
   You can also create or modify it manually:
   ```bash
   # .env file
   FLUIDNC_IP=10.0.0.246
   ```

## Running the Application

You can run this application either directly or using Docker.

### Direct Method

1. Create and activate a virtual environment:
   ```bash
   python -m venv fluidnc-ledscreen
   source fluidnc-ledscreen/bin/activate
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the script (LED matrix requires sudo):
   ```bash
   sudo -E env PATH=$PATH python3 fluidnc_monitor.py
   ```

### Docker Method (Recommended)

1. Build and run using docker-compose:
   ```bash
   docker-compose up --build -d
   ```

2. View logs:
   ```bash
   docker-compose logs -f
   ```

3. Stop the container:
   ```bash
   docker-compose down
   ```

### Configuration

Edit the `config` file to set your FluidNC machine's IP address and update interval:
   ```ini
   [FluidNC]
   ip_address = <your-fluidnc-ip>
   update_interval = 0.05  # Updates every 50ms
   ```

Or when using Docker, set the IP in docker-compose.yml:
   ```yaml
   environment:
     - FLUIDNC_IP=10.0.0.246
   ```

### Features

- Real-time position monitoring via WebSocket
- LED matrix display showing:
  - Machine state
  - X, Y, Z coordinates
  - Status updates
- Automatic reconnection
- 50ms refresh rate
- Test pattern on startup
- Container health monitoring
- Automatic log rotation
- Hardware access via GPIO

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

### Management Scripts

The following scripts are available in the `scripts` directory:

- `./scripts/start.sh` - Start the container (creates .env if needed)
- `./scripts/stop.sh` - Stop the container
- `./scripts/restart.sh` - Restart the container
- `./scripts/logs.sh` - View container logs
- `./scripts/update.sh` - Update to latest version
- `./scripts/cleanup.sh` - Clean up Docker resources
- `./scripts/create-env.sh` - Create/update .env file

First time setup:
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Create .env file (if needed)
./scripts/create-env.sh

# Start the container
./scripts/start.sh
```

Example usage:
```bash
./scripts/start.sh    # Start the container
./scripts/logs.sh     # View logs
./scripts/stop.sh     # Stop the container
```

Note: The application will automatically create a `.env` file based on your config file when starting. You only need to run create-env.sh manually if you want to update the environment variables. 