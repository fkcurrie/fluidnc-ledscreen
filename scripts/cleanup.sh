#!/bin/bash
echo "Cleaning up Docker resources..."
docker-compose down -v
docker system prune -f
echo "Cleanup complete." 