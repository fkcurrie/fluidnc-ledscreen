#!/bin/bash
echo "Restarting FluidNC LED Monitor and Web Interface..."
docker-compose down
docker-compose up -d
echo "All containers restarted."
echo "- LED Monitor is running"
echo "- Web Interface available at http://$(hostname -I | cut -d' ' -f1):5000"
echo "Use './scripts/logs.sh' to view logs." 