#!/bin/bash
echo "Updating FluidNC LED Monitor..."
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo "Update complete. Use './scripts/logs.sh' to view logs." 