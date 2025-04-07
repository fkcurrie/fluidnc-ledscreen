# FluidNC LED Screen Monitor

A Python application that displays FluidNC status on an LED matrix display.

## Setup and Usage

### Prerequisites

1. Raspberry Pi with a 64x32 RGB LED Matrix panel
2. Docker and Docker Compose installed
3. FluidNC controller running and accessible on the network

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/fkcurrie/fluidnc-ledscreen.git
   cd fluidnc-ledscreen
   ```

2. Configure the application:
   - Edit `config/fluidnc_config.ini` to set your FluidNC IP address
   - If no IP is specified, the application will attempt to discover it automatically

3. Build and start the containers:
   ```bash
   # First time setup
   docker-compose build
   docker-compose up -d

   # For subsequent updates
   docker-compose build fluidnc-monitor
   docker-compose up -d fluidnc-monitor
   ```

4. View the logs:
   ```bash
   docker-compose logs -f fluidnc-monitor
   ```

### Troubleshooting

1. If the display doesn't show:
   - Check the logs for any errors
   - Verify the LED matrix panel is properly connected
   - Ensure the user has permissions to access the GPIO pins

2. If coordinates don't update:
   - Verify FluidNC is running and accessible
   - Check the IP address configuration
   - Review the logs for connection issues

3. If the display shows incorrect data:
   - Verify the FluidNC configuration
   - Check if the machine is properly homed
   - Review the logs for parsing errors

## Project Structure

```
.
├── fluidnc_monitor.py    # Main application code
├── docker-compose.yml    # Container orchestration
├── logging_config.py    # Logging configuration
├── requirements.txt     # Python dependencies
├── config/             # Configuration directory
│   └── fluidnc_config.ini  # Main configuration file
├── fluidnc-monitor/    # Docker build files
│   ├── Dockerfile.base    # Base image definition
│   └── Dockerfile        # Service image definition
├── logs/               # Log files directory (ignored by git)
├── .dockerignore       # Docker build exclusions
├── .gitignore         # Git exclusions
└── README.md          # Documentation
```

## Features

- Real-time display of FluidNC machine status
- Shows X, Y, Z coordinates with color coding
- Displays connection status and IP address
- Automatic discovery of FluidNC device
- Configurable via INI file

## Notes

### Working Solutions

1. Coordinate Updates
   - Status requests are sent every 0.5 seconds to ensure immediate updates
   - Keep-alive ping is sent every 5 seconds
   - Display is refreshed before and after each status update
   - WebSocket timeout is set to 0.1 seconds for responsive message handling

2. Display Layout
   - IP address shown at top right
   - Coordinates (X, Y, Z) displayed vertically on left with color coding:
     - X: Red
     - Y: Green
     - Z: Blue
   - Status text shown on same line as Z coordinate
   - Connection dot flashes green when connected

3. Security Updates (April 2024)
   - Updated Flask to 2.3.3 to fix session cookie disclosure vulnerability
   - Updated Werkzeug to 3.0.6 to fix multipart data parsing vulnerability
   - Updated Jinja2 to 3.1.6 to fix HTML attribute injection vulnerability
   - Updated Gunicorn to 23.0.0 to fix HTTP request smuggling vulnerability
   - Updated MarkupSafe to 2.1.5 for improved security
   - Updated Click to 8.1.7 for improved security
   - All dependencies are now at their latest secure versions
   - Dependabot alerts are being monitored and addressed promptly
   - Security updates are tested in Docker containers before deployment
   - Fixed code scanning alert for stack trace exposure in web/app.py

### Known Issues

1. None currently - all features working as expected

### Future Improvements

1. Add support for more status information (feed rate, spindle speed, etc.)
2. Add configuration for update frequencies
3. Add support for different display layouts
4. Add support for different color schemes

## Development Notes

### Current Implementation (April 2025)

The application has reached a stable state with the following working features:

1. WebSocket Communication
   - Stable connection to FluidNC on port 81
   - Automatic reconnection on disconnection
   - Keep-alive messages every 5 seconds
   - Status requests every 0.5 seconds for immediate updates
   - WebSocket timeout of 0.1 seconds for responsive updates

2. Status Parsing
   - Flexible key-value parser for status messages
   - Handles variations in message format
   - Extracts machine state and position data
   - Ignores non-status messages (PING, ID)
   - Real-time coordinate updates with proper formatting

3. LED Matrix Display
   - 64x32 RGB LED Matrix panel support
   - Color-coded coordinate display (X: Red, Y: Green, Z: Blue)
   - Real-time updates with immediate refresh
   - Clean layout with IP at top right and status on Z coordinate line
   - Flashing green connection indicator

4. Configuration
   - INI file-based configuration
   - Support for static IP or automatic discovery
   - Configurable update intervals
   - Docker-based deployment for easy setup

### Technical Details

1. WebSocket Implementation
   - Uses `websocket-client` library
   - Handles connection drops gracefully
   - Maintains persistent connection
   - Processes messages asynchronously
   - Implements proper error handling and reconnection logic

2. Display Implementation
   - Uses `adafruit_blinka_raspberry_pi5_piomatter` for LED control
   - Custom font rendering for text
   - Efficient buffer management
   - Proper cleanup on exit
   - Optimized display refresh timing

3. Status Processing
   - Parses messages in format `<State|Key:Value|Key:Value...>`
   - Handles missing fields gracefully
   - Updates display immediately on new data
   - Maintains state between updates
   - Properly formats coordinates with one decimal place

### Build Process

The project uses a multi-stage build process for faster development:

1. Base Image (`fluidnc-monitor/Dockerfile.base`):
   - Contains all system dependencies and Python packages
   - Downloads and sets up fonts
   - Rebuild only when dependencies change: `docker-compose build base`

2. Monitor Service:
   - Uses the base image for faster builds
   - Contains only application code
   - Quick rebuild: `docker-compose build fluidnc-monitor`

3. Development Workflow:
   - First time setup: `docker-compose build`
   - Regular development: `docker-compose build fluidnc-monitor && docker-compose up -d fluidnc-monitor`
   - View logs: `docker-compose logs -f fluidnc-monitor`

### Key Improvements

1. Coordinate Updates
   - Implemented frequent status requests (every 0.5 seconds)
   - Added display refresh before and after updates
   - Optimized WebSocket timeout for responsiveness
   - Ensured proper message parsing and display updates

2. Display Layout
   - IP address positioned at top right
   - Coordinates displayed vertically on left
   - Color-coded axes (X: Red, Y: Green, Z: Blue)
   - Status text aligned with Z coordinate
   - Flashing connection indicator

3. Performance Optimizations
   - Reduced WebSocket timeout to 0.1 seconds
   - Implemented efficient display buffer management
   - Added proper cleanup on exit
   - Optimized message parsing

## License

[Add your chosen license here]
