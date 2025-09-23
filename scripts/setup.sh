#!/bin/bash

# Flight Compensation Claim API - Development Setup Script
# This script sets up the complete development environment

set -e  # Exit on any error

echo "🚀 Setting up Flight Compensation Claim API development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi

    print_status "Docker and Docker Compose are installed ✓"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11 or higher."
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    REQUIRED_VERSION="3.11"
    
    if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
        print_error "Python $PYTHON_VERSION is installed, but Python $REQUIRED_VERSION or higher is required."
        exit 1
    fi

    print_status "Python $PYTHON_VERSION is installed ✓"
}

# Create virtual environment
setup_virtual_env() {
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    else
        print_status "Virtual environment already exists ✓"
    fi

    print_status "Activating virtual environment..."
    source venv/bin/activate

    print_status "Upgrading pip..."
    pip install --upgrade pip
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
}

# Set up environment file
setup_env_file() {
    if [ ! -f ".env" ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_warning "Please review and update the .env file with your configuration"
    else
        print_status ".env file already exists ✓"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p uploads
    mkdir -p logs
    mkdir -p alembic/versions
}

# Set up PostgreSQL with Docker
setup_postgres() {
    print_status "Setting up PostgreSQL with Docker..."
    
    # Stop any existing containers
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    
    # Start PostgreSQL and Redis
    print_status "Starting PostgreSQL and Redis containers..."
    docker-compose -f docker-compose.dev.yml up -d postgres redis
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    timeout=60
    while ! docker exec flight_claim_postgres_dev pg_isready -U flight_claim_user -d flight_claim_db >/dev/null 2>&1; do
        sleep 1
        timeout=$((timeout - 1))
        if [ $timeout -eq 0 ]; then
            print_error "PostgreSQL failed to start within 60 seconds"
            exit 1
        fi
    done
    
    print_status "PostgreSQL is ready ✓"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Check if alembic is initialized
    if [ ! -f "alembic.ini" ]; then
        print_status "Initializing Alembic..."
        alembic init alembic
    fi
    
    # Create initial migration if it doesn't exist
    if [ ! -f "alembic/versions/001_initial_migration.py" ]; then
        print_status "Creating initial migration..."
        # Copy the pre-created migration
        cp alembic/versions/001_initial_migration.py alembic/versions/001_initial_migration.py.bak 2>/dev/null || true
    fi
    
    # Apply migrations
    print_status "Applying database migrations..."
    alembic upgrade head
    
    print_status "Database migrations completed ✓"
}

# Test database connection
test_database() {
    print_status "Testing database connection..."
    
    # Create a simple test script
    cat > test_db.py << 'EOF'
from sqlalchemy import create_engine
from app.config import settings

try:
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("✓ Database connection successful")
        conn.close()
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    exit(1)
EOF

    python test_db.py
    rm test_db.py
}

# Set up pre-commit hooks (optional)
setup_pre_commit() {
    if command -v pre-commit &> /dev/null; then
        print_status "Setting up pre-commit hooks..."
        pre-commit install
    else
        print_warning "pre-commit is not installed. Skipping pre-commit setup."
        print_status "To install: pip install pre-commit"
    fi
}

# Create sample data (optional)
create_sample_data() {
    read -p "Do you want to create sample data? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Creating sample data..."
        
        # Create a simple script to add sample data
        cat > create_sample_data.py << 'EOF'
import asyncio
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Claim
from datetime import datetime, date

async def create_sample_data():
    db: Session = next(get_db())
    
    try:
        # Create sample users
        users = [
            User(email="test@example.com", booking_reference="ABC123", is_admin=False),
            User(email="admin@flightclaim.com", booking_reference="ADMIN001", is_admin=True),
        ]
        
        for user in users:
            existing = db.query(User).filter(User.email == user.email).first()
            if not existing:
                db.add(user)
        
        db.commit()
        
        # Create sample claims
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if test_user:
            claims = [
                Claim(
                    claim_id="CL001234",
                    user_id=test_user.id,
                    full_name="Test User",
                    email="test@example.com",
                    booking_reference="ABC123",
                    flight_number="LH1234",
                    planned_departure_date=date(2024, 1, 15),
                    status="under_review"
                ),
                Claim(
                    claim_id="CL001235",
                    user_id=test_user.id,
                    full_name="Test User",
                    email="test@example.com",
                    booking_reference="ABC123",
                    flight_number="BA4567",
                    planned_departure_date=date(2024, 1, 16),
                    status="approved"
                )
            ]
            
            for claim in claims:
                existing = db.query(Claim).filter(Claim.claim_id == claim.claim_id).first()
                if not existing:
                    db.add(claim)
            
            db.commit()
        
        print("✓ Sample data created successfully")
        
    except Exception as e:
        print(f"✗ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_sample_data())
EOF

        python create_sample_data.py
        rm create_sample_data.py
    fi
}

# Main setup function
main() {
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║        Flight Compensation Claim API - Development Setup            ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo
    
    # Check prerequisites
    check_docker
    check_python
    
    # Setup steps
    setup_virtual_env
    install_dependencies
    setup_env_file
    create_directories
    setup_postgres
    run_migrations
    test_database
    setup_pre_commit
    create_sample_data
    
    echo
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║                    🎉 Setup Complete! 🎉                            ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo
    echo "Next steps:"
    echo "1. Review and update your .env file if needed"
    echo "2. Start the development server: python run.py"
    echo "3. Visit http://localhost:8000/docs for API documentation"
    echo "4. Visit http://localhost:8080 for database management (Adminer)"
    echo
    echo "To stop the services: docker-compose -f docker-compose.dev.yml down"
    echo "To start again: docker-compose -f docker-compose.dev.yml up -d"
    echo
    print_status "Happy coding! 🚀"
}

# Run the setup
main "$@"