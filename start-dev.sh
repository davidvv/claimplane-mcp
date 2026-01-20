#!/bin/bash

# Development Environment Startup Script
# This script starts all services needed for local development

set -e  # Exit on any error

echo "=================================================="
echo "Starting EasyAirClaim Development Environment"
echo "=================================================="

# Start Nextcloud services first (file storage infrastructure)
echo ""
echo "[1/4] Starting Nextcloud services..."
docker compose -f docker-compose.nextcloud.yml up -d

# Wait for Nextcloud to be healthy
echo "Waiting for Nextcloud to be healthy..."
until [ "`docker inspect -f {{.State.Health.Status}} nextcloud`"=="healthy" ]; do
    echo "Still waiting for Nextcloud... (this might take a minute on first run)"
    sleep 5
    if [ "$(docker inspect -f {{.State.Status}} nextcloud)" != "running" ]; then
        echo "❌ Nextcloud failed to start!"
        exit 1
    fi
    # Timeout after 2 minutes
    ((c++)) && ((c==24)) && break
done

# Start main application services
echo ""
echo "[2/4] Starting Flight Claim application services..."
docker compose up -d

# Wait for services to be healthy
echo "Waiting for application services to be ready..."
sleep 5
until [ "`docker inspect -f {{.State.Health.Status}} flight_claim_db`"=="healthy" ]; do
    echo "Waiting for Database..."
    sleep 2
done

# Start Vite development server
echo ""
echo "[3/4] Starting Vite development server (Port 3000)..."
cd frontend_Claude45
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# We use --host to make it accessible to the Cloudflare Tunnel
npm run dev -- --host &
VITE_PID=$!
cd ..

# NOTE: Production mode uses nginx on Port 80
# To use the pre-built production frontend instead:
# 1. Comment out the Vite section above
# 2. Ensure nginx is running in docker-compose.yml
# 3. Update Cloudflare Tunnel to point to Port 80 instead of 3000


# Show current logs briefly
echo ""
echo "[4/4] Tailening logs to check for errors..."
sleep 5
docker compose logs --tail=20 api


echo ""
echo "=================================================="
echo "✅ All services started successfully!"
echo "=================================================="
echo ""
echo "Service URLs:"
echo "  Frontend (Vite Dev):     http://localhost:3000"
echo "  API (FastAPI):           http://localhost:8000"
echo "  API Docs:                http://localhost:8000/docs"
echo "  Nginx (Production):      http://localhost:80"
echo "  Nextcloud:               http://localhost:8081"
echo ""
echo "Docker Services:"
docker ps --filter "name=flight_claim" --filter "name=nextcloud" --format "  - {{.Names}}: {{.Status}}"
echo ""
echo "=================================================="
echo ""
echo "📝 DEVELOPMENT MODE: Using Vite dev server (port 3000)"
echo "   For production: Build frontend and use nginx (port 80)"
echo "   Command: cd frontend_Claude45 && npm run build"
echo ""
echo "To stop all services:"
echo "  docker compose down"
echo "  docker compose -f docker-compose.nextcloud.yml down"
echo "  kill $VITE_PID  # Stop Vite server"
echo ""
echo "Press Ctrl+C to stop the Vite server (Docker services will keep running)"
echo "=================================================="

# Keep script running and forward Vite logs
wait $VITE_PID
