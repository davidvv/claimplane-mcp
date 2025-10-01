# Troubleshooting Guide

## Flight Claim System - Common Issues and Solutions

This guide provides systematic solutions for common issues encountered when developing, deploying, or operating the Flight Claim System. Issues are organized by category with detailed diagnostic steps and solutions.

## Quick Diagnostic Commands

Before diving into specific issues, use these commands to get system status:

```bash
# System Status Overview
curl http://localhost/health                    # Basic API health
curl http://localhost/health/detailed          # Detailed system info
docker-compose ps                             # Service status
docker-compose logs --tail=50 api            # Recent API logs
docker-compose logs --tail=50 db             # Recent database logs
```

## Database Issues

### Issue 1: Database Connection Refused

**Symptoms**:
```
sqlalchemy.exc.OperationalError: connection refused
FATAL: database "flight_claim" does not exist
Error: could not connect to server: Connection refused
```

**Diagnostic Steps**:
```bash
# Check if database container is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test direct connection
docker exec -it flight_claim_db psql -U postgres -l
```

**Solutions**:

#### Solution A: Database Not Started
```bash
# Start database service
docker-compose up -d db

# Wait for initialization (first time only)
sleep 30

# Verify database is ready
docker-compose logs db | grep "database system is ready to accept connections"
```

#### Solution B: Database Not Initialized
```bash
# Stop all services
docker-compose down

# Remove database volume to reset
docker-compose down -v

# Restart services (database will reinitialize)
docker-compose up -d

# Wait for complete initialization
docker-compose logs -f db
```

#### Solution C: Wrong Connection String
```bash
# Check environment variables
docker-compose exec api env | grep DATABASE_URL

# Correct format should be:
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/flight_claim

# Update docker-compose.yml if incorrect
```

### Issue 2: Database Migration Failures

**Symptoms**:
```
asyncpg.exceptions.UndefinedTableError: relation "customers" does not exist
sqlalchemy.exc.ProgrammingError: table already exists
```

**Diagnostic Steps**:
```bash
# Check if tables exist
docker exec flight_claim_db psql -U postgres -d flight_claim -c "\dt"

# Check table schemas
docker exec flight_claim_db psql -U postgres -d flight_claim -c "\d customers"
```

**Solutions**:

#### Solution A: Initialize Database Schema
```bash
# Run initialization script
docker-compose exec api python init_db.py

# Or manually create tables
docker exec flight_claim_db psql -U postgres -d flight_claim -f /path/to/schema.sql
```

#### Solution B: Reset Database Completely
```bash
# Backup data if needed
docker exec flight_claim_db pg_dump -U postgres flight_claim > backup.sql

# Reset database
docker-compose down
docker volume rm flight_claim_postgres_data
docker-compose up -d

# Wait for reinitialization
docker-compose logs -f db
```

### Issue 3: PATCH Field Overwriting (RESOLVED)

**Previous Symptoms**:
```
# PATCH requests were overwriting existing fields with "string" values
# Only updating email would set firstName, lastName, phone to "string"
# Address fields also affected by similar issues
```

**Status**: ✅ **FIXED** - This issue has been resolved in the current version.

**What Was Fixed**:
- Enhanced `Customer.address` property to properly handle None values
- Improved `CustomerResponseSchema` with explicit Optional field types
- Added better null-safety in PATCH endpoint address handling
- Fixed serialization issues that caused "string" placeholder values

**Current Behavior**:
- ✅ PATCH requests only update provided fields
- ✅ Existing data is preserved for omitted fields
- ✅ Address fields are handled correctly during partial updates
- ✅ No more "string" value overwrites

**Diagnostic Steps** (if issue reoccurs):
```bash
# Enable detailed logging to trace PATCH operations
docker-compose logs -f api | grep -E "(PATCH|UPDATE|address)"

# Test specific scenarios
curl -X PATCH "http://localhost/customers/{id}" \
  -H "Content-Type: application/json" \
  -d '{"email": "new@example.com"}'

# Verify only email field was updated
curl "http://localhost/customers/{id}"
```

**Prevention**:
- The current implementation properly handles None values
- Address property correctly checks for non-None values before serialization
- Response schema explicitly marks optional fields as Optional
```

## API Validation Issues

### Issue 4: Email Validation Errors

**Symptoms**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": ["Invalid email format"]
  }
}
```

**Diagnostic Steps**:
```bash
# Test with various email formats
curl -X POST "http://localhost/customers" \
  -H "Content-Type: application/json" \
  -d '{"email": "test", "firstName": "Test", "lastName": "User"}'

# Check validation logs
docker-compose logs api | grep "email"
```

**Solutions**:

#### Solution A: Fix Email Format
```bash
# Use valid email format
curl -X POST "http://localhost/customers" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "firstName": "Test", "lastName": "User"}'
```

#### Solution B: Handle Empty Email in PATCH
```python
# CustomerPatchSchema handles empty emails correctly
@validator('email', pre=True)
def handle_empty_email(cls, v):
    if v == "" or (isinstance(v, str) and v.strip() == ""):
        return None  # Convert empty strings to None
    return v
```

### Issue 5: Field Length Validation Failures

**Symptoms**:
```json
{
  "error": {
    "details": [
      {
        "field": "firstName",
        "message": "ensure this value has at most 50 characters",
        "type": "value_error.any_str.max_length"
      }
    ]
  }
}
```

**Solutions**:

#### Solution A: Adjust Field Lengths
```python
# Check field constraints in schemas
class CustomerCreateSchema(BaseModel):
    first_name: str = Field(..., max_length=50, alias="firstName")
    last_name: str = Field(..., max_length=50, alias="lastName")
    phone: Optional[str] = Field(None, max_length=20)
```

#### Solution B: Truncate Long Values
```bash
# Truncate data before sending
LONG_NAME="Very Long Name That Exceeds Fifty Characters Limit"
TRUNCATED_NAME=${LONG_NAME:0:50}
```

### Issue 6: Airport Code Validation

**Symptoms**:
```json
{
  "error": {
    "message": "Airport code must be 3 characters"
  }
}
```

**Solutions**:

#### Solution A: Use Valid IATA Codes
```bash
# Use 3-character IATA airport codes
curl -X POST "http://localhost/claims" \
  -d '{
    "customerId": "uuid",
    "flightInfo": {
      "departureAirport": "JFK",
      "arrivalAirport": "LAX"
    }
  }'
```

#### Solution B: Auto-Convert to Uppercase
```python
# Model validator handles case conversion
@validates('departure_airport', 'arrival_airport')
def validate_airport_code(self, key, code):
    if code and len(code) != 3:
        raise ValueError("Airport code must be 3 characters")
    return code.upper()  # Automatically uppercase
```

## Docker and Container Issues

### Issue 7: Port Already in Use

**Symptoms**:
```
ERROR: for nginx  Cannot start service nginx: Ports are not available: listen tcp 0.0.0.0:80: bind: address already in use
```

**Diagnostic Steps**:
```bash
# Check what's using the port
sudo netstat -tlnp | grep :80
sudo lsof -i :80

# On macOS:
lsof -i :80
```

**Solutions**:

#### Solution A: Use Different Ports
```yaml
# docker-compose.override.yml
services:
  nginx:
    ports:
      - "8080:80"  # Use port 8080 instead
  api:
    ports:
      - "8001:8000"
```

#### Solution B: Stop Conflicting Service
```bash
# Stop Apache if running
sudo systemctl stop apache2

# Or kill specific process
sudo kill -9 <PID>
```

### Issue 8: Container Build Failures

**Symptoms**:
```
ERROR: failed to solve: process "/bin/sh -c pip install -r requirements.txt" did not complete successfully: exit code 1
```

**Diagnostic Steps**:
```bash
# Check build context
docker-compose build --progress=plain api

# Test requirements installation locally
pip install -r requirements.txt
```

**Solutions**:

#### Solution A: Clear Build Cache
```bash
# Remove cached layers
docker-compose build --no-cache api

# Clean up Docker system
docker system prune -f
```

#### Solution B: Fix Requirements
```bash
# Update Python dependencies
pip freeze > requirements.txt

# Or fix specific dependency
pip install --upgrade fastapi
```

### Issue 9: Container Health Check Failures

**Symptoms**:
```
health check failed: unhealthy
Container exits with code 1
```

**Diagnostic Steps**:
```bash
# Check container status
docker-compose ps

# Check health check logs
docker-compose logs api | grep "health"

# Manual health check
docker-compose exec api curl -f http://localhost:8000/health
```

**Solutions**:

#### Solution A: Fix Health Check Endpoint
```python
# Ensure health endpoint is accessible
@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
```

#### Solution B: Adjust Health Check Settings
```dockerfile
# More lenient health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

## Application Runtime Issues

### Issue 10: Import Errors

**Symptoms**:
```
ModuleNotFoundError: No module named 'app'
ImportError: cannot import name 'customers_router' from 'app.routers'
```

**Diagnostic Steps**:
```bash
# Check Python path
docker-compose exec api python -c "import sys; print(sys.path)"

# Test imports
docker-compose exec api python -c "from app.main import app; print('Import successful')"
```

**Solutions**:

#### Solution A: Fix PYTHONPATH
```dockerfile
# Ensure correct working directory
WORKDIR /app
ENV PYTHONPATH=/app
```

#### Solution B: Fix Import Statements
```python
# Use relative imports correctly
from app.routers import customers_router, claims_router
# Not: from routers import customers_router
```

### Issue 11: Database Session Leaks

**Symptoms**:
```
WARNING: Connection pool is full, discarding connection
SQLAlchemy connection pool exhausted
```

**Diagnostic Steps**:
```bash
# Monitor connection count
docker exec flight_claim_db psql -U postgres -d flight_claim -c "SELECT count(*) FROM pg_stat_activity;"

# Check for leaked connections
docker-compose logs api | grep "connection"
```

**Solutions**:

#### Solution A: Proper Session Management
```python
# Ensure session is properly closed
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()  # Always close
```

#### Solution B: Increase Pool Size
```python
# Adjust connection pool settings
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # Increase pool size
    max_overflow=30,     # Allow more overflow connections
    pool_timeout=30      # Timeout for getting connection
)
```

### Issue 12: PUT/PATCH Behavioral Differences

**Previous Symptoms**:
```
# PATCH was overwriting existing fields with "string" values
# Address fields not handled correctly in partial updates
# Serialization issues causing data corruption
```

**Status**: ✅ **RESOLVED** - These behavioral issues have been fixed.

**Current Behavior**:
- ✅ **PUT**: Complete updates work correctly, null values properly handled
- ✅ **PATCH**: Only updates provided fields, preserves existing data
- ✅ **Address fields**: Properly handled in both PUT and PATCH operations
- ✅ **No data corruption**: Fixed serialization issues that caused "string" overwrites

**Diagnostic Steps** (if issues reoccur):
```bash
# Test PUT with null values
curl -X PUT "http://localhost/customers/uuid" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "firstName": "Test", "lastName": "User", "phone": null}'

# Test PATCH partial update
curl -X PATCH "http://localhost/customers/uuid" \
  -H "Content-Type: application/json" \
  -d '{"firstName": "Updated"}'

# Verify address handling
curl -X PATCH "http://localhost/customers/uuid" \
  -H "Content-Type: application/json" \
  -d '{"address": {"street": "New Street"}}'
```

**Key Improvements Made**:
- Enhanced null-safety in Customer model address property
- Improved response schema with explicit Optional types
- Better address field handling in PATCH endpoint
- Fixed serialization issues that caused placeholder values

## Performance Issues

### Issue 13: Slow API Response Times

**Symptoms**:
```
# API responses taking >5 seconds
# Timeout errors from clients
```

**Diagnostic Steps**:
```bash
# Test response times
time curl http://localhost/customers

# Check database query performance
docker exec flight_claim_db psql -U postgres -d flight_claim -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;"
```

**Solutions**:

#### Solution A: Add Database Indexes
```sql
-- Common performance indexes
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers (email);
CREATE INDEX IF NOT EXISTS idx_claims_customer_id ON claims (customer_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims (status);
CREATE INDEX IF NOT EXISTS idx_claims_departure_date ON claims (departure_date);
```

#### Solution B: Optimize Queries
```python
# Use efficient queries with joins
async def get_customer_with_claims(self, customer_id: UUID):
    stmt = select(Customer).options(
        selectinload(Customer.claims)  # Eager load to avoid N+1
    ).where(Customer.id == customer_id)
    
    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()
```

#### Solution C: Implement Pagination
```python
# Always use pagination for large datasets
async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
    # Enforce reasonable limits
    limit = min(limit, 1000)
    
    stmt = select(self.model).offset(skip).limit(limit)
    result = await self.session.execute(stmt)
    return result.scalars().all()
```

### Issue 14: High Memory Usage

**Symptoms**:
```
# Docker containers using excessive memory
# Out of Memory (OOM) kills
```

**Diagnostic Steps**:
```bash
# Check container memory usage
docker stats

# Check Python memory usage
docker-compose exec api python -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
"
```

**Solutions**:

#### Solution A: Limit Container Memory
```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

#### Solution B: Optimize Database Connections
```python
# Reduce connection pool size
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,        # Reduce from 20
    max_overflow=20,     # Reduce from 30
    pool_recycle=1800    # Recycle connections more frequently
)
```

## Network and CORS Issues

### Issue 15: CORS Errors

**Symptoms**:
```javascript
// Browser console error
Access to XMLHttpRequest at 'http://localhost:8000/customers' 
from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solutions**:

#### Solution A: Configure CORS Properly
```python
# main.py CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)
```

#### Solution B: Development CORS Settings
```python
# For development only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 16: Nginx Proxy Issues

**Symptoms**:
```
502 Bad Gateway
nginx: [emerg] host not found in upstream "api"
```

**Diagnostic Steps**:
```bash
# Check nginx configuration
docker-compose exec nginx nginx -t

# Check if API is accessible from nginx
docker-compose exec nginx curl http://api:8000/health
```

**Solutions**:

#### Solution A: Fix Nginx Configuration
```nginx
# nginx.conf
upstream api_backend {
    server api:8000;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Solution B: Ensure Service Dependencies
```yaml
# docker-compose.yml
services:
  nginx:
    depends_on:
      - api  # Ensure API starts before nginx
```

## Debugging Tools and Techniques

### Enable Debug Logging

```python
# main.py - Add debug logging
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add to endpoints
logger.debug(f"Received request: {request_data}")
```

### Database Query Logging

```python
# database.py - Enable SQL logging
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Enable SQL query logging
    echo_pool=True  # Enable connection pool logging
)
```

### Request/Response Logging

```python
# middleware.py - Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.2f}s")
    return response
```

### Development Debugging

```bash
# Run with debugging enabled
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up

# Connect debugger (if configured)
docker-compose exec api python -m pdb app/main.py
```

## Recovery Procedures

### Complete System Reset

```bash
#!/bin/bash
# reset_system.sh - Complete system reset

echo "Stopping all services..."
docker-compose down

echo "Removing volumes..."
docker-compose down -v

echo "Cleaning up containers and images..."
docker system prune -f

echo "Rebuilding services..."
docker-compose build --no-cache

echo "Starting services..."
docker-compose up -d

echo "Waiting for services to be ready..."
sleep 30

echo "Verifying system health..."
curl http://localhost/health

echo "System reset complete!"
```

### Data Recovery from Backup

```bash
# Restore database from backup
docker-compose down
docker volume rm flight_claim_postgres_data
docker-compose up -d db
sleep 30
docker exec -i flight_claim_db psql -U postgres flight_claim < backup.sql
docker-compose up -d
```

This troubleshooting guide covers the most common issues encountered in the Flight Claim System and provides systematic approaches to diagnose and resolve them.