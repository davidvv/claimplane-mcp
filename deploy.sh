#!/bin/bash

# ClaimPlane Deployment Script
# Called by GitHub Actions on push to MVP branch
#
# ROLLBACK PROCEDURE (manual):
# If deployment fails, run these commands:
#   cd /home/david/claimplane/claimplane
#   git reset --hard HEAD~1  # Go back to previous commit
#   docker-compose down && docker-compose up -d --build
#   cd frontend_Claude45 && npm run build

set -e  # Exit on any error

# Configuration
MAX_HEALTH_RETRIES=30
HEALTH_RETRY_INTERVAL=5
API_HEALTH_URL="http://localhost:8000/health"

# Project directory - can be overridden via environment variable
# Default path matches the webhook container volume mount
PROJECT_DIR="${PROJECT_DIR:-/home/david/claimplane/claimplane}"

# Ensure we are in the project root (mounted volume)
cd "$PROJECT_DIR" || { echo "Project directory not found: $PROJECT_DIR"; exit 1; }

echo "=========================================="
echo "Starting deployment at $(date)"
echo "=========================================="

# Store current commit for potential rollback
PREVIOUS_COMMIT=$(git rev-parse HEAD)
echo "Previous commit: $PREVIOUS_COMMIT"

# Pull latest changes
echo "Pulling latest code..."
git pull origin MVP

CURRENT_COMMIT=$(git rev-parse HEAD)
echo "Current commit: $CURRENT_COMMIT"

# Backend deployment
echo "Rebuilding Docker containers..."
docker-compose down
docker-compose up -d --build

# Health check with retries
echo "Waiting for API to be healthy..."
HEALTH_CHECK_PASSED=false
for i in $(seq 1 $MAX_HEALTH_RETRIES); do
    if curl -sf "$API_HEALTH_URL" > /dev/null 2>&1; then
        HEALTH_CHECK_PASSED=true
        echo "✓ API health check passed (attempt $i/$MAX_HEALTH_RETRIES)"
        break
    fi
    echo "  Waiting for API... (attempt $i/$MAX_HEALTH_RETRIES)"
    sleep $HEALTH_RETRY_INTERVAL
done

if [ "$HEALTH_CHECK_PASSED" = false ]; then
    echo "✗ API health check failed after $MAX_HEALTH_RETRIES attempts"
    echo ""
    echo "ROLBACK INSTRUCTIONS:"
    echo "  git reset --hard $PREVIOUS_COMMIT"
    echo "  docker-compose down && docker-compose up -d --build"
    echo "  cd frontend_Claude45 && npm run build"
    exit 1
fi

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✓ Backend services are running"
else
    echo "✗ Backend services failed to start"
    exit 1
fi

# Frontend deployment
echo "Deploying frontend..."
cd frontend_Claude45

# Install dependencies if package.json changed
if git diff HEAD@{1} HEAD --name-only | grep -q "package.json"; then
    echo "package.json changed, running npm install..."
    npm install
fi

# Build frontend
echo "Building frontend..."
npm run build

echo ""
echo "=========================================="
echo "✓ Deployment completed successfully at $(date)"
echo "=========================================="
