#!/bin/bash
echo "Restarting FluidNC LED Monitor..."
docker-compose down
docker-compose up -d
echo "Container restarted. Use './scripts/logs.sh' to view logs." 