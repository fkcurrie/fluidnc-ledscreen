#!/bin/bash

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    ./scripts/create-env.sh
fi

echo "Starting FluidNC LED Monitor and Web Interface..."
docker-compose --env-file .env up -d
echo "Containers started."
echo "- LED Monitor is running"
echo "- Web Interface available at http://$(hostname -I | cut -d' ' -f1):5000"
echo "Use './scripts/logs.sh' to view logs." 