# Setup & Deployment Guide

## Flight Claim System - Complete Setup and Deployment Documentation

This guide provides step-by-step instructions for setting up the Flight Claim System in various environments, from local development to production deployment using Docker.

## Prerequisites

### System Requirements

**Operating System**:
- Linux (Ubuntu 20.04+ recommended)
- macOS (10.15+ with Homebrew)
- Windows 10/11 (with WSL2 recommended)

**Required Software**:
- Python 3.11+ 
- PostgreSQL 15+ (for local development)
- Docker 20.10+ and Docker Compose 2.0+
- Git 2.30+

**Hardware Recommendations**:
- **Development**: 8GB RAM, 2 CPU cores, 10GB disk space
- **Production**: 16GB+ RAM, 4+ CPU cores, 50GB+ disk space

### Development Tools (Optional but Recommended)

- **IDE**: VS Code, PyCharm, or similar
- **API Testing**: Postman, Insomnia, or curl
- **Database Tools**: pgAdmin, DBeaver, or psql
- **Version Control**: Git with GitHub/GitLab

## Local Development Setup

### 1. Environment Preparation

#### Clone Repository
```bash
git clone <repository-url>
cd flight_claim
```

#### Python Environment Setup
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

# Verify Python version
python --version  # Should show Python 3.11.x
```

#### Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
```

### 2. Database Setup (Local PostgreSQL)

#### Install PostgreSQL

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS (Homebrew)**:
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Windows**:
Download and install from [PostgreSQL Official Site](https://www.postgresql.org/download/windows/)

#### Create Database and User
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE flight_claim;
CREATE USER flight_claim_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE flight_claim TO flight_claim_user;

# Enable UUID extension
\c flight_claim;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# Exit PostgreSQL
\q
```

### 3. Redis Setup (Phase 2 - Required for Email Notifications)

#### Install Redis

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Verify installation
redis-cli ping  # Should return PONG
```

**macOS (Homebrew)**:
```bash
brew install redis
brew services start redis

# Verify installation
redis-cli ping  # Should return PONG
```

**Windows**:
- Download Redis for Windows from https://github.com/microsoftarchive/redis/releases
- Or use WSL2 with Linux installation above

#### Test Redis Connection
```bash
# Connect to Redis
redis-cli

# Test basic operations
SET test "hello"
GET test
# Should return "hello"

# Exit Redis CLI
exit
```

#### Start Celery Worker (Local Development)
```bash
# Make sure you're in the project directory with virtual environment activated
# Start Celery worker in a separate terminal
celery -A app.celery_app worker --loglevel=info

# You should see output showing:
# - Worker started
# - Connected to redis://localhost:6379
# - Registered tasks: send_claim_submitted_email, send_status_update_email, send_document_rejected_email
```

**Note**: For local development, you need both the FastAPI server AND the Celery worker running:
- Terminal 1: `uvicorn app.main:app --reload` (API server)
- Terminal 2: `celery -A app.celery_app worker --loglevel=info` (Background worker)

### 4. Environment Configuration

#### Create Environment File
```bash
# Copy example environment file
cp .env.example .env

# Edit environment variables
nano .env
```

#### Environment Variables (`.env`) - Updated Phase 2
```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://flight_claim_user:your_secure_password@localhost:5432/flight_claim

# Redis Configuration (Phase 2)
REDIS_URL=redis://localhost:6379

# Celery Configuration (Phase 2)
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379

# Email/SMTP Configuration (Phase 2)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password-here
SMTP_FROM_EMAIL=noreply@claimplane.com
NOTIFICATIONS_ENABLED=true

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=info
DEBUG=true

# Security (generate secure keys for production)
SECRET_KEY=your-secret-key-here

# Server Configuration
HOST=0.0.0.0
PORT=8000

# CORS Settings (adjust for production)
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

**Phase 2 Additions**:
- **REDIS_URL**: Redis connection for Celery task queue
- **SMTP Settings**: Gmail SMTP for email notifications (requires App Password)
- **NOTIFICATIONS_ENABLED**: Toggle email notifications on/off

### 4. Database Initialization

#### Initialize Database Schema
```bash
# Run database initialization script
python init_db.py

# Or use the database initialization function directly
python -c "
import asyncio
from app.database import init_db
asyncio.run(init_db())
"
```

#### Verify Database Setup
```bash
# Connect to database and verify tables
psql -U flight_claim_user -d flight_claim -h localhost

# List tables
\dt

# Check customers table structure
\d customers

# Check claims table structure
\d claims

# Exit
\q
```

### 5. Run Application

#### Start Development Server
```bash
# Method 1: Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Method 2: Using Python module
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Method 3: Using main.py
python app/main.py
```

#### Verify Application
```bash
# Check API health
curl http://localhost:8000/health

# Check API info
curl http://localhost:8000/info

# Access interactive documentation
# Open in browser: http://localhost:8000/docs
```

### 6. Development Workflow

#### Running Tests
```bash
# Install test dependencies (if not in requirements.txt)
pip install pytest pytest-asyncio httpx

# Run comprehensive API tests
python test_api.py

# Run specific test files
python test_final_comprehensive.py
```

#### Code Quality Checks
```bash
# Install development tools
pip install black isort flake8 mypy

# Format code
black app/
isort app/

# Check code style
flake8 app/

# Type checking
mypy app/
```

## Docker Deployment

### 1. Quick Start with Docker Compose

#### Prerequisites Check
```bash
# Verify Docker installation
docker --version  # Should show Docker version 20.10+
docker-compose --version  # Should show version 2.0+

# Verify Docker daemon is running
docker info
```

#### One-Command Deployment
```bash
# Clone repository (if not already done)
git clone <repository-url>
cd flight_claim

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Verify Deployment
```bash
# Check API health
curl http://localhost/health

# Access Swagger UI
# Open in browser: http://localhost/docs

# Check database connectivity
curl http://localhost/health/db
```

### 2. Docker Compose Configuration (Updated Phase 2)

#### Service Overview
```yaml
# docker-compose.yml structure
services:
  db:             # PostgreSQL 15 database
  redis:          # Redis for Celery broker (Phase 2)
  celery_worker:  # Celery background worker (Phase 2)
  api:            # FastAPI application
  nginx:          # Reverse proxy and load balancer (optional)
```

**Phase 2 Additions**:
- **Redis**: Message broker and result backend for Celery task queue
- **Celery Worker**: Background worker for async email notifications

#### Database Service Configuration
```yaml
db:
  image: postgres:15-alpine
  container_name: flight_claim_db
  environment:
    POSTGRES_DB: flight_claim
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
```

#### Redis Service Configuration (Phase 2)
```yaml
redis:
  image: redis:7-alpine
  container_name: flight_claim_redis
  ports:
    - "6379:6379"
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 3s
    retries: 5
  restart: unless-stopped
```

**Purpose**: Redis serves as the message broker and result backend for Celery task queue
**Health Check**: Verifies Redis is accepting connections before starting dependent services
**Persistence**: By default uses in-memory storage; add volume for persistence if needed

#### Celery Worker Service Configuration (Phase 2)
```yaml
celery_worker:
  build: .
  container_name: flight_claim_celery
  command: celery -A app.celery_app worker --loglevel=info
  environment:
    DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/flight_claim
    REDIS_URL: redis://redis:6379
    CELERY_BROKER_URL: redis://redis:6379
    CELERY_RESULT_BACKEND: redis://redis:6379
    # SMTP Configuration for Email Notifications
    SMTP_HOST: smtp.gmail.com
    SMTP_PORT: 587
    SMTP_USERNAME: ${SMTP_USERNAME}
    SMTP_PASSWORD: ${SMTP_PASSWORD}
    SMTP_FROM_EMAIL: noreply@claimplane.com
    NOTIFICATIONS_ENABLED: true
  depends_on:
    redis:
      condition: service_healthy
    db:
      condition: service_healthy
  restart: unless-stopped
```

**Purpose**: Background worker for async email notifications (claim submitted, status updates, document rejections)
**Task Types**:
- `send_claim_submitted_email`
- `send_status_update_email`
- `send_document_rejected_email`

**Monitoring Celery Worker**:
```bash
# View worker logs
docker-compose logs -f celery_worker

# Check worker status
docker-compose exec celery_worker celery -A app.celery_app inspect active

# See registered tasks
docker-compose exec celery_worker celery -A app.celery_app inspect registered
```

**SMTP Configuration**:
For Gmail SMTP, you need to:
1. Enable 2-factor authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Set `SMTP_USERNAME` to your Gmail address
4. Set `SMTP_PASSWORD` to the generated App Password

#### API Service Configuration (Updated Phase 2)
```yaml
api:
  build: .
  container_name: flight_claim_api
  environment:
    DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/flight_claim
    REDIS_URL: redis://redis:6379  # Phase 2
    ENVIRONMENT: development
    # SMTP Configuration for Email Notifications (Phase 2)
    SMTP_HOST: smtp.gmail.com
    SMTP_PORT: 587
    SMTP_USERNAME: ${SMTP_USERNAME}
    SMTP_PASSWORD: ${SMTP_PASSWORD}
    SMTP_FROM_EMAIL: noreply@claimplane.com
    NOTIFICATIONS_ENABLED: true
  ports:
    - "8000:8000"
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy  # Phase 2
  volumes:
    - ./app:/app/app  # For development hot-reload
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Phase 2 Updates**:
- Added `REDIS_URL` for Celery task queue
- Added SMTP environment variables for email notifications
- Added dependency on Redis service health check

#### Nginx Service Configuration
```yaml
nginx:
  image: nginx:alpine
  container_name: flight_claim_nginx
  ports:
    - "80:80"
  depends_on:
    - api
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
```

### 3. Custom Docker Build

#### Dockerfile Analysis
```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim as builder

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production image
FROM python:3.11-slim

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Application setup
WORKDIR /app
COPY app/ ./app/
COPY init_db.py .

# Non-root user for security
RUN useradd --create-home --shell /bin/bash app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Build Custom Image
```bash
# Build image
docker build -t flight-claim-api:latest .

# Run with custom image
docker run -d \
  --name flight-claim-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/flight_claim \
  flight-claim-api:latest
```

### 4. Production Docker Configuration

#### Environment-Specific Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: flight_claim
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    networks:
      - flight-claim-network

  api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@db:5432/flight_claim
      ENVIRONMENT: ${ENVIRONMENT:-production}
      LOG_LEVEL: ${LOG_LEVEL:-warning}
      SECRET_KEY: ${SECRET_KEY}
      FILE_ENCRYPTION_KEY: ${FILE_ENCRYPTION_KEY}
      NEXTCLOUD_URL: ${NEXTCLOUD_URL}
      NEXTCLOUD_USERNAME: ${NEXTCLOUD_USERNAME}
      NEXTCLOUD_PASSWORD: ${NEXTCLOUD_PASSWORD}
      REDIS_URL: ${REDIS_URL}
      VIRUS_SCAN_ENABLED: ${VIRUS_SCAN_ENABLED:-true}
      CLAMAV_URL: ${CLAMAV_URL}
      RATE_LIMIT_UPLOAD: ${RATE_LIMIT_UPLOAD:-5/minute}
      RATE_LIMIT_DOWNLOAD: ${RATE_LIMIT_DOWNLOAD:-50/minute}
      JWT_EXPIRATION_MINUTES: ${JWT_EXPIRATION_MINUTES:-30}
      JWT_REFRESH_EXPIRATION_DAYS: ${JWT_REFRESH_EXPIRATION_DAYS:-7}
      CORS_ORIGINS: ${CORS_ORIGINS}
      SECURITY_HEADERS_ENABLED: ${SECURITY_HEADERS_ENABLED:-true}
      FILE_RETENTION_DAYS: ${FILE_RETENTION_DAYS:-365}
      NEXTCLOUD_TIMEOUT: ${NEXTCLOUD_TIMEOUT:-30}
      NEXTCLOUD_MAX_RETRIES: ${NEXTCLOUD_MAX_RETRIES:-3}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - flight-claim-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: unless-stopped
    networks:
      - flight-claim-network

networks:
  flight-claim-network:
    driver: bridge

volumes:
  postgres_data:
```

#### Production Environment Variables
```bash
# .env.prod - Generated using scripts/generate_secrets.py
DB_USER=flight_claim_prod
DB_PASSWORD=ultra_secure_password_here
DATABASE_URL=postgresql+asyncpg://flight_claim_prod:ultra_secure_password_here@db:5432/flight_claim
ENVIRONMENT=production
LOG_LEVEL=warning
DEBUG=false
SECRET_KEY=production-secret-key-min-32-chars
FILE_ENCRYPTION_KEY=your-32-character-encryption-key-here
NEXTCLOUD_URL=https://your-nextcloud-domain.com
NEXTCLOUD_USERNAME=admin
NEXTCLOUD_PASSWORD=secure-nextcloud-password
REDIS_URL=redis://:secure-redis-password@redis:6379/0
VIRUS_SCAN_ENABLED=true
CLAMAV_URL=clamav:3310
RATE_LIMIT_UPLOAD=5/minute
RATE_LIMIT_DOWNLOAD=50/minute
JWT_EXPIRATION_MINUTES=30
JWT_REFRESH_EXPIRATION_DAYS=7
CORS_ORIGINS=["https://yourdomain.com"]
SECURITY_HEADERS_ENABLED=true
FILE_RETENTION_DAYS=365
NEXTCLOUD_TIMEOUT=30
NEXTCLOUD_MAX_RETRIES=3
```

#### Generate Production Secrets
```bash
# Generate secure production secrets
python scripts/generate_secrets.py

# This creates .env.production with cryptographically secure secrets
# Copy to your production environment
cp .env.production .env.prod

# Update domain-specific settings
sed -i 's/yourdomain.com/your-actual-domain.com/g' .env.prod
```

#### Deploy Production
```bash
# Deploy with production configuration and secure secrets
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Monitor deployment
docker-compose -f docker-compose.prod.yml logs -f

# Verify security configuration
docker-compose -f docker-compose.prod.yml exec api env | grep -E "(ENVIRONMENT|SECURITY_HEADERS_ENABLED|VIRUS_SCAN_ENABLED)"
```

## Advanced Configuration

### 1. SSL/HTTPS Setup

#### Generate SSL Certificates (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot

# Generate certificates
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/
```

#### Nginx SSL Configuration
```nginx
# nginx.ssl.conf
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Database Backup and Recovery

#### Automated Backup Script
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="flight_claim"

# Create backup
docker exec flight_claim_db pg_dump -U postgres $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Keep only last 7 backups
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql"
```

#### Restore Database
```bash
# Restore from backup
docker exec -i flight_claim_db psql -U postgres flight_claim < backup_20240115_120000.sql
```

### 3. Monitoring and Logging

#### Docker Logging Configuration
```yaml
# docker-compose.yml logging section
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        tag: "flight-claim-api"
```

#### Log Aggregation
```bash
# View logs from all services
docker-compose logs -f

# View specific service logs
docker-compose logs -f api

# Export logs
docker-compose logs --no-color api > app.log
```

### 4. Performance Optimization

#### Database Performance Tuning
```sql
-- Add indexes for common queries
CREATE INDEX idx_customers_email ON customers (email);
CREATE INDEX idx_claims_customer_id ON claims (customer_id);
CREATE INDEX idx_claims_status ON claims (status);
CREATE INDEX idx_claims_departure_date ON claims (departure_date);
```

#### Application Performance
```python
# Connection pool optimization in database.py
engine = create_async_engine(
    DATABASE_URL,
    echo=False,           # Disable SQL logging in production
    pool_size=20,         # Number of permanent connections
    max_overflow=50,      # Additional connections when needed
    pool_timeout=30,      # Timeout for getting connection
    pool_recycle=3600,    # Recycle connections every hour
    pool_pre_ping=True    # Validate connections before use
)
```

## Verification and Testing

### 1. System Health Verification

#### Health Check Script
```bash
#!/bin/bash
# health_check.sh

BASE_URL="http://localhost"

echo "=== Flight Claim System Health Check ==="

# Basic health check
echo "1. Checking basic health..."
curl -f $BASE_URL/health || echo "❌ Basic health check failed"

# Database health check
echo "2. Checking database connectivity..."
curl -f $BASE_URL/health/db || echo "❌ Database health check failed"

# API functionality test
echo "3. Testing API endpoints..."

# Create test customer
CUSTOMER=$(curl -s -X POST $BASE_URL/customers \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "firstName": "Test",
    "lastName": "User"
  }')

if [[ $CUSTOMER == *"id"* ]]; then
  echo "✅ Customer creation successful"
else
  echo "❌ Customer creation failed"
fi

echo "=== Health Check Complete ==="
```

### 2. Load Testing

#### Simple Load Test
```bash
# Install apache bench
sudo apt install apache2-utils

# Test API performance
ab -n 1000 -c 10 http://localhost/health

# Test with POST requests
ab -n 100 -c 5 -p customer_data.json -T application/json http://localhost/customers
```

#### Load Test with Python
```python
# load_test.py
import asyncio
import aiohttp
import time

async def test_endpoint(session, url):
    async with session.get(url) as response:
        return response.status

async def load_test():
    url = "http://localhost/health"
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = [test_endpoint(session, url) for _ in range(100)]
        responses = await asyncio.gather(*tasks)
    
    end_time = time.time()
    success_count = sum(1 for status in responses if status == 200)
    
    print(f"Completed 100 requests in {end_time - start_time:.2f} seconds")
    print(f"Success rate: {success_count}/100 ({success_count}%)")

if __name__ == "__main__":
    asyncio.run(load_test())
```

## Troubleshooting Common Issues

### 1. Database Connection Issues

#### Problem: "Connection refused" errors
```bash
# Check if database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test database connectivity
docker exec -it flight_claim_db psql -U postgres -d flight_claim
```

#### Solution: Database not ready
```bash
# Wait for database to be fully ready
docker-compose up -d db
sleep 30  # Wait for initialization
docker-compose up -d api
```

### 2. Port Conflicts

#### Problem: "Port already in use" errors
```bash
# Check what's using the port
sudo netstat -tlnp | grep :80
sudo lsof -i :8000

# Kill process using the port
sudo kill -9 <PID>
```

#### Solution: Use different ports
```yaml
# docker-compose.override.yml
services:
  nginx:
    ports:
      - "8080:80"  # Use port 8080 instead of 80
  api:
    ports:
      - "8001:8000"  # Use port 8001 instead of 8000
```

### 3. Permission Issues

#### Problem: Docker permission denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or use sudo with docker commands
sudo docker-compose up -d
```

### 4. Application Won't Start

#### Check Application Logs
```bash
# View detailed logs
docker-compose logs -f api

# Check for Python errors
docker-compose exec api python -c "from app.main import app; print('Import successful')"
```

#### Common Fixes
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Reset database
docker-compose down -v
docker-compose up -d
```

### 5. API Response Issues

#### Debug API Problems
```bash
# Test with verbose curl
curl -v http://localhost/health

# Check CORS issues
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS http://localhost/customers
```

## Maintenance and Updates

### 1. Application Updates

#### Update Process
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --pull
docker-compose up -d

# Verify update
curl http://localhost/info
```

### 2. Database Migrations

#### Using Alembic (if implemented)
```bash
# Generate migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head
```

### 3. Backup Procedures

#### Regular Backup Schedule
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
```

This comprehensive setup and deployment guide provides everything needed to run the Flight Claim System in any environment, from local development to production deployment.