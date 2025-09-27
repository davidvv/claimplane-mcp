# Flight Claim System API

A modular Python/FastAPI backend for managing flight compensation claims. This system provides user management, claim submission, and tracking capabilities with a clean, scalable architecture.

## Features

- **User Management**: Customer registration and profile management
- **Claim Management**: Flight claim submission and tracking
- **Repository Pattern**: Clean data access layer
- **Input Validation**: Comprehensive request validation
- **Error Handling**: Robust error handling and responses
- **Health Checks**: System and database health monitoring
- **Docker Support**: Containerized deployment ready

## Tech Stack

- **FastAPI**: Modern, fast web framework
- **SQLAlchemy 2.0**: Async ORM for database operations
- **PostgreSQL**: Primary database
- **Pydantic**: Data validation and serialization
- **Docker**: Containerization
- **Nginx**: Reverse proxy

## Project Structure

```
flight_claim/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # Database configuration
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── exceptions.py           # Custom exceptions
│   ├── middleware.py           # Error handling middleware
│   ├── repositories/           # Repository pattern implementation
│   │   ├── __init__.py
│   │   ├── base.py              # Base repository class
│   │   ├── customer_repository.py
│   │   └── claim_repository.py
│   └── routers/                # API route handlers
│       ├── __init__.py
│       ├── customers.py
│       ├── claims.py
│       └── health.py
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Multi-container setup
├── nginx.conf                  # Nginx configuration
├── .env                        # Environment variables
└── test_api.py                 # API test script
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Using Docker (Recommended)

1. **Clone and setup**:
   ```bash
   # The project is already set up in your current directory
   ```

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```

3. **Verify deployment**:
   ```bash
   # Check health endpoint
   curl http://localhost/health
   
   # Or visit http://localhost/docs for interactive API documentation
   ```

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup PostgreSQL**:
   ```bash
   # Using Docker for PostgreSQL
   docker run -d \
     --name flight_claim_db \
     -e POSTGRES_DB=flight_claim \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=postgres \
     -p 5432:5432 \
     postgres:15-alpine
   ```

3. **Run the application**:
   ```bash
   python app/main.py
   ```

4. **Access the API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

## API Endpoints

### Customers
- `POST /customers` - Create new customer
- `GET /customers/{customer_id}` - Get customer by ID
- `GET /customers` - List customers (paginated)
- `GET /customers/search/by-email/{email}` - Search customers by email
- `GET /customers/search/by-name/{name}` - Search customers by name

### Claims
- `POST /claims` - Create claim for existing customer
- `POST /claims/submit` - Submit claim with customer info
- `GET /claims/{claim_id}` - Get claim by ID
- `GET /claims` - List claims (with optional filtering)
- `GET /claims/customer/{customer_id}` - Get claims for customer
- `GET /claims/status/{status}` - Get claims by status

### System
- `GET /health` - Basic health check
- `GET /health/db` - Database health check
- `GET /health/detailed` - Detailed system health
- `GET /` - API information
- `GET /info` - Detailed API information

## Testing

Run the comprehensive test script:

```bash
python test_api.py
```

This will test all major endpoints and verify the system is working correctly.

## Data Models

### Customer
- `id` (UUID): Unique identifier
- `email` (str): Email address (unique)
- `first_name` (str): First name
- `last_name` (str): Last name
- `phone` (str, optional): Phone number
- `address` (object, optional): Address information
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

### Claim
- `id` (UUID): Unique identifier
- `customer_id` (UUID): Foreign key to customer
- `flight_number` (str): Flight number
- `airline` (str): Airline name
- `departure_date` (date): Flight departure date
- `departure_airport` (str): Departure airport (IATA code)
- `arrival_airport` (str): Arrival airport (IATA code)
- `incident_type` (str): Type of incident (delay, cancellation, denied_boarding, baggage_delay)
- `status` (str): Claim status (draft, submitted, under_review, approved, rejected, paid, closed)
- `compensation_amount` (decimal, optional): Compensation amount
- `currency` (str): Currency code (default: EUR)
- `notes` (str, optional): Additional notes
- `submitted_at` (datetime): Submission timestamp
- `updated_at` (datetime): Last update timestamp

## Configuration

Environment variables can be configured in the `.env` file:

- `ENVIRONMENT`: Application environment (development/production)
- `DATABASE_URL`: PostgreSQL connection string
- `LOG_LEVEL`: Logging level
- `SECRET_KEY`: Secret key for security features (future use)

## Development

### Adding New Features

1. **Models**: Add new SQLAlchemy models in `app/models.py`
2. **Schemas**: Create Pydantic schemas in `app/schemas.py`
3. **Repositories**: Implement repository classes in `app/repositories/`
4. **Routers**: Add API endpoints in `app/routers/`
5. **Tests**: Update `test_api.py` with new endpoint tests

### Database Migrations

For production deployments, consider using Alembic for database migrations:

```bash
# Install Alembic
pip install alembic

# Initialize migrations
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

## Production Deployment

1. **Security**: Update CORS settings, add authentication
2. **Database**: Use managed PostgreSQL service
3. **Monitoring**: Add logging and monitoring
4. **Scaling**: Configure load balancing and auto-scaling
5. **Backups**: Implement database backup strategy

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## License

Private - All rights reserved.

## Support

For support, contact: easyairclaim@gmail.com