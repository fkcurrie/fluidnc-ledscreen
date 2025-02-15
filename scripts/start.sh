#!/bin/bash

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    ./scripts/create-env.sh
fi

echo "Starting FluidNC LED Monitor..."
docker-compose --env-file .env up -d
echo "Container started. Use './scripts/logs.sh' to view logs." 