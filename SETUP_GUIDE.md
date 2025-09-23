# PostgreSQL Setup Guide - Flight Compensation Claim API

## Quick Start with Docker 🐳

The easiest way to set up PostgreSQL for development is using Docker. I've already configured everything for you!

### Option 1: Full Development Stack (Recommended)

This sets up PostgreSQL, Redis, the API, and Adminer (database management tool) all at once:

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Check if everything is running
docker-compose -f docker-compose.dev.yml ps

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop everything
docker-compose -f docker-compose.dev.yml down
```

**What's included:**
- PostgreSQL 15 on port 5432
- Redis 7 on port 6379  
- Flight Claim API on port 8000
- Adminer (database GUI) on port 8080

### Option 2: Just PostgreSQL

If you only want the database:

```bash
# Start PostgreSQL container
docker run -d \
  --name flight_claim_postgres \
  -e POSTGRES_DB=flight_claim_db \
  -e POSTGRES_USER=flight_claim_user \
  -e POSTGRES_PASSWORD=flight_claim_password \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine

# Check if it's running
docker ps

# Connect to the database
docker exec -it flight_claim_postgres psql -U flight_claim_user -d flight_claim_db
```

## Database Connection Details

**Connection String:**
```
postgresql://flight_claim_user:flight_claim_password@localhost:5432/flight_claim_db
```

**Environment Variables (add to your .env file):**
```bash
DATABASE_URL=postgresql://flight_claim_user:flight_claim_password@localhost:5432/flight_claim_db
```

## Setting Up the Database Schema

### Method 1: Using Alembic Migrations (Recommended)

```bash
# Install Alembic if not already installed
pip install alembic

# Initialize Alembic (if not done)
alembic init alembic

# Create the initial migration (if not created)
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head

# Check current migration status
alembic current

# View migration history
alembic history
```

### Method 2: Direct Database Creation

If you want to create the tables directly without migrations:

```bash
# Start Python shell
python

# Run this code
from app.database import create_tables, init_db
create_tables()
init_db()
```

## Verifying the Setup

### 1. Check Database Connection
```bash
# Test connection
docker exec -it flight_claim_postgres psql -U flight_claim_user -d flight_claim_db -c "\dt"

# You should see tables like:
# public | users                  | table | flight_claim_user
# public | claims                 | table | flight_claim_user
# public | documents              | table | flight_claim_user
# public | claim_status_history   | table | flight_claim_user
# public | chat_sessions          | table | flight_claim_user
# public | chat_messages          | table | flight_claim_user
```

### 2. Test with Adminer
Open http://localhost:8080 in your browser and connect with:
- **System:** PostgreSQL
- **Server:** postgres
- **Username:** flight_claim_user
- **Password:** flight_claim_password
- **Database:** flight_claim_db

### 3. Test API Connection
```bash
# Start your API
python run.py

# Test health endpoint
curl http://localhost:8000/health

# Should return:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "timestamp": "2024-01-20T10:30:00Z",
#   "database": "healthy"
# }
```

## Development Workflow

### Daily Development
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Work on your code...
# The API will auto-reload when you make changes

# View logs
docker-compose -f docker-compose.dev.yml logs -f api

# Stop when done
docker-compose -f docker-compose.dev.yml down
```

### Database Management
```bash
# Access database CLI
docker exec -it flight_claim_postgres psql -U flight_claim_user -d flight_claim_db

# Backup database
docker exec flight_claim_postgres pg_dump -U flight_claim_user flight_claim_db > backup.sql

# Restore database
docker exec -i flight_claim_postgres psql -U flight_claim_user -d flight_claim_db < backup.sql

# Reset database (WARNING: This deletes all data!)
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs flight_claim_postgres

# Test connection manually
docker exec -it flight_claim_postgres psql -U flight_claim_user -d flight_claim_db -c "SELECT 1;"
```

### Port Conflicts
If port 5432 is already in use:
```bash
# Use a different port in docker-compose.dev.yml
ports:
  - "5433:5432"  # Map to different host port
```

### Permission Issues
```bash
# Fix permissions on uploads directory
sudo chown -R $USER:$USER uploads/

# Or delete and recreate
rm -rf uploads/
mkdir uploads
```

## Production Considerations

For production deployment:

1. **Use stronger passwords**
2. **Enable SSL/TLS**
3. **Set up regular backups**
4. **Configure connection pooling**
5. **Monitor database performance**
6. **Use managed database services** (AWS RDS, Google Cloud SQL, etc.)

## Alternative: Local PostgreSQL Installation

If you prefer not to use Docker, you can install PostgreSQL locally:

### macOS (with Homebrew)
```bash
brew install postgresql
brew services start postgresql
createdb flight_claim_db
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb flight_claim_db
```

### Windows
Download and install from: https://www.postgresql.org/download/windows/

Then update your `.env` file with the appropriate connection string.

## Next Steps

Once your database is running:

1. **Apply database migrations:**
   ```bash
   alembic upgrade head
   ```

2. **Start the API:**
   ```bash
   python run.py
   ```

3. **Test the API:**
   - Visit http://localhost:8000/docs for Swagger UI
   - Visit http://localhost:8000/redoc for ReDoc
   - Use Adminer at http://localhost:8080 to manage the database

4. **Run the frontend update** following the `frontend_update_plan.md`

Your PostgreSQL database is now ready to work with the Flight Compensation Claim API! 🎉