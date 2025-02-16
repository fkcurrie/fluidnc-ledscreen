#!/bin/bash

echo "Stopping all containers..."
docker-compose down

echo "Removing all project containers and volumes..."
docker-compose rm -fsv

echo "Removing project images..."
docker rmi fluidnc-ledscreen-fluidnc-monitor fluidnc-ledscreen-web-interface

echo "Cleaning up any dangling images..."
docker system prune -f

echo "Cleanup complete. Run ./scripts/start.sh to rebuild and start fresh."