#!/bin/bash

# Development Environment Startup Script
# This script starts all services needed for local development

set -e  # Exit on any error

echo "=================================================="
echo "Starting EasyAirClaim Development Environment"
echo "=================================================="

# Start Nextcloud services first (file storage infrastructure)
echo ""
echo "[1/3] Starting Nextcloud services..."
docker compose -f docker-compose.nextcloud.yml up -d

# Wait a bit for Nextcloud DB to be ready
echo "Waiting for Nextcloud database to be healthy..."
sleep 10

# Start main application services
echo ""
echo "[2/3] Starting Flight Claim application services..."
docker compose up -d

# Wait for services to be healthy
echo "Waiting for application services to be ready..."
sleep 15

# Start Vite development server
# NOTE: In production, use nginx (already configured in docker-compose.yml)
#       The nginx container serves the built frontend from frontend_Claude45/dist
#       For production deployment, run: npm run build && docker compose restart nginx
echo ""
echo "[3/3] Starting Vite development server..."
cd frontend_Claude45
npm run dev &
VITE_PID=$!
cd ..

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
