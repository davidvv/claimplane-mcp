#!/bin/bash

# ClaimPlane Deployment Script
# Called by GitHub Actions on push to MVP branch

set -e  # Exit on any error

echo "Starting deployment at $(date)"

# Pull latest changes
echo "Pulling latest code..."
git pull origin MVP

# Backend deployment
echo "Rebuilding Docker containers..."
docker-compose down
docker-compose up -d --build

# Wait for services to be healthy
echo "Waiting for services to start..."
sleep 10

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

echo "Deployment completed successfully at $(date)"
