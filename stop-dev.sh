#!/bin/bash

# Development Environment Shutdown Script
# This script stops all services

set -e  # Exit on any error

echo "=================================================="
echo "Stopping ClaimPlane Development Environment"
echo "=================================================="

# Stop Vite dev server if running
echo ""
echo "[1/3] Stopping Vite dev server..."
pkill -f "vite" || echo "  No Vite server running"

# Stop main application services
echo ""
echo "[2/3] Stopping Flight Claim application services..."
docker compose down

# Stop Nextcloud services
echo ""
echo "[3/3] Stopping Nextcloud services..."
docker compose -f docker-compose.nextcloud.yml down

echo ""
echo "=================================================="
echo "✅ All services stopped successfully!"
echo "=================================================="
echo ""
echo "To restart, run: ./start-dev.sh"
echo ""
