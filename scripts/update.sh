#!/bin/bash
echo "Updating FluidNC LED Monitor and Web Interface..."
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo "Update complete."
echo "- LED Monitor is running"
echo "- Web Interface available at http://$(hostname -I | cut -d' ' -f1):5000"
echo "Use './scripts/logs.sh' to view logs." 