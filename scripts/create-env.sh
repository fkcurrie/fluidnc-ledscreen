#!/bin/bash
echo "Creating .env file..."

# Default values
DEFAULT_IP="10.0.0.246"

# Read from config file if it exists
if [ -f "config" ]; then
    IP=$(grep "ip_address" config | cut -d "=" -f2 | tr -d ' ')
    if [ ! -z "$IP" ]; then
        DEFAULT_IP=$IP
    fi
fi

# Create .env file
cat > .env << EOF
FLUIDNC_IP=$DEFAULT_IP
EOF

echo ".env file created with FLUIDNC_IP=$DEFAULT_IP" 