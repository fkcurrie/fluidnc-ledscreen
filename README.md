# RGB Matrix Panel Controller

This project controls RGB LED matrix panels using a ** Raspberry Pi 5 **.

## Required Hardware

### Core Components
1. Raspberry Pi 5
   - [PiShop.ca](https://www.pishop.ca/product/raspberry-pi-5-8gb/) - 8GB Model
   - [BuyaPi.ca](https://buyapi.ca/product/raspberry-pi-5-8gb/) - 8GB Model
   - [Chicago Electronic Distributors](https://chicagodist.com/products/raspberry-pi-5) - US Option

2. RGB Matrix Bonnet for Raspberry Pi
   - [Adafruit](https://www.adafruit.com/product/3211) - Official Source
   - [Digikey](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3211/6580122)

3. 64x32 RGB LED Matrix Panel - 4mm Pitch
   - [Adafruit](https://www.adafruit.com/product/2278) - 64x32 RGB LED Matrix
   - [Digikey](https://www.digikey.com/en/products/detail/adafruit-industries-llc/2278/5356253)

### Power Supplies
1. Official Raspberry Pi 5 Power Supply (27W USB-C)
   - [PiShop.ca](https://www.pishop.ca/product/raspberry-pi-5-27w-psu-white-na/) - North America
   - [BuyaPi.ca](https://buyapi.ca/product/raspberry-pi-5-27w-power-supply-white-na/) - North America

2. 5V 3A (or higher) Power Supply for LED Matrix
   - [Adafruit](https://www.adafruit.com/product/1466) - 5V 4A Power Supply
   - [Digikey](https://www.digikey.com/en/products/detail/mean-well-usa-inc/GST25U05-P1J/7703710)

### Accessories
1. microSD Card (32GB+ recommended)
   - [PiShop.ca](https://www.pishop.ca/product/samsung-evo-plus-32gb-microsd-card-with-adapter/) - Samsung EVO+
   - [BuyaPi.ca](https://buyapi.ca/product/samsung-evo-plus-32gb-microsdhc-with-adapter-100mb-s/)

2. Active Cooling Case (recommended for Pi 5)
   - [PiShop.ca](https://www.pishop.ca/product/raspberry-pi-5-active-cooling-case/)
   - [BuyaPi.ca](https://buyapi.ca/product/raspberry-pi-5-active-cooling-case/)

## Setup & Installation

For detailed hardware and software setup instructions, please refer to the official Adafruit guide:
[RGB Matrix Panels with Raspberry Pi 5](https://learn.adafruit.com/rgb-matrix-panels-with-raspberry-pi-5)

## Configuration

Configuration details can be found in the official documentation linked above. Make sure to follow the wiring and software setup instructions carefully.

## Usage

This application can be run either directly on your Raspberry Pi or via Docker.

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

3. Configure your FluidNC IP address:
   ```bash
   # Edit config file
   nano config
   ```
   ```ini
   [FluidNC]
   ip_address = <your-fluidnc-ip>
   update_interval = 0.05  # Updates every 50ms
   ```

4. Run the script (LED matrix requires sudo):
   ```bash
   sudo -E env PATH=$PATH python3 fluidnc_monitor.py
   ```

### Docker Method (Recommended)

1. First-time setup:
   ```bash
   # Make management scripts executable
   chmod +x scripts/*.sh

   # Create environment file
   ./scripts/create-env.sh
   ```

2. Start the container:
   ```bash
   ./scripts/start.sh
   ```

3. View logs:
   ```bash
   ./scripts/logs.sh
   ```

4. Stop the container:
   ```bash
   ./scripts/stop.sh
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

### Example Output

#### Video Demo
[![FluidNC LED Matrix Display Demo](https://img.youtube.com/vi/jGGGwgc2lLE/0.jpg)](https://youtu.be/jGGGwgc2lLE)

*Click image to watch video demonstration*

The LED matrix display shows:
1. Machine state at the top (e.g., "Idle", "Run", "Hold")
2. Real-time position coordinates:
   - X position in red
   - Y position in green
   - Z position in blue
3. White border around the display

Terminal output example:
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

For video demonstrations of the display in action, check the project's releases page.

### Troubleshooting

If you encounter issues:
1. Check your FluidNC IP address is correct
2. Verify LED matrix connections
3. Ensure proper permissions for GPIO access
4. Check container logs for errors
5. Verify network connectivity to FluidNC

For hardware-specific issues, refer to the Adafruit guide linked in the Setup section.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your chosen license here] 
