#!/bin/bash

# Flight Compensation Claim API - Development Start Script
# Quick script to start the development environment

set -e

echo "🚀 Starting Flight Compensation Claim API development environment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start the development stack
print_status "Starting PostgreSQL, Redis, and API services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait a moment for services to start
sleep 5

# Check if services are healthy
print_status "Checking service health..."

# Check PostgreSQL
if docker exec flight_claim_postgres_dev pg_isready -U flight_claim_user -d flight_claim_db >/dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL is not responding"
    exit 1
fi

# Check Redis
if docker exec flight_claim_redis_dev redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not responding"
    exit 1
fi

# Check API
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ API is running"
else
    echo "⚠️  API might still be starting up..."
fi

echo ""
echo "🎉 Development environment is ready!"
echo ""
echo "📍 Services available:"
echo "   • API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Database Admin: http://localhost:8080"
echo ""
echo "🔧 Useful commands:"
echo "   • View logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "   • Stop services: docker-compose -f docker-compose.dev.yml down"
echo "   • Restart API: docker-compose -f docker-compose.dev.yml restart api"
echo ""
echo "Happy coding! 🚀"