#!/bin/bash

# Flight Compensation Claim API - Development Stop Script
# Quick script to stop the development environment

echo "🛑 Stopping Flight Compensation Claim API development environment..."

# Stop all services
docker-compose -f docker-compose.dev.yml down

echo "✅ Development environment stopped."

# Optional: Remove volumes (WARNING: This deletes all data!)
if [[ "$1" == "--clean" ]]; then
    echo "🧹 Cleaning up volumes (this will delete all data)..."
    docker-compose -f docker-compose.dev.yml down -v
    echo "✅ Volumes cleaned."
fi

echo ""
echo "To start again, run: ./scripts/start-dev.sh"