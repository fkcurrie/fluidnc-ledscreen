#!/bin/bash

if [ "$1" = "web" ]; then
    echo "Showing Web Interface logs (Ctrl+C to exit)..."
    docker-compose logs -f web-interface
elif [ "$1" = "led" ]; then
    echo "Showing LED Monitor logs (Ctrl+C to exit)..."
    docker-compose logs -f fluidnc-monitor
else
    echo "Showing all logs (Ctrl+C to exit)..."
    docker-compose logs -f 
fi 