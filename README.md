# Flight Compensation Claim API

A FastAPI-based backend service for handling flight delay compensation claims under EU Regulation 261/2004.

## Features

- **OpenAPI 3.1.0 Compliant**: Full implementation of the OpenAPI specification
- **PostgreSQL Database**: Robust data persistence with SQLAlchemy ORM
- **Authentication & Authorization**: JWT-based authentication with role-based access
- **File Upload**: Secure document upload with validation and storage
- **Chatbot Integration**: AI-powered chat assistant for claim guidance
- **Admin Dashboard**: Comprehensive admin interface for claim management
- **Comprehensive Logging**: Structured logging with multiple log levels
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **CORS Support**: Configurable CORS for frontend integration
- **Database Migrations**: Alembic-based database schema management

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis (optional, for background tasks)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/flightclaim/api.git
cd flight_claim_api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Set up the database:
```bash
# Create database
createdb flight_claim_db

# Run migrations
alembic upgrade head

# Or create tables directly
python -c "from app.database import create_tables; create_tables()"
```

6. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Endpoints

### Claims
- `POST /api/flight-details` - Submit flight details
- `POST /api/personal-info` - Submit personal information
- `POST /api/upload` - Upload supporting documents
- `GET /api/claim-status` - Get claim status
- `POST /api/claims` - Create complete claim

### Authentication
- `POST /api/auth/login` - User login (OAuth2)
- `POST /api/auth/login-json` - Alternative login with JSON
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh access token

### Chat
- `POST /api/chat/send` - Send chat message
- `POST /api/chat/sessions` - Create chat session
- `GET /api/chat/sessions/{session_id}/history` - Get chat history
- `DELETE /api/chat/sessions/{session_id}` - Delete chat session

### Admin
- `GET /api/admin/claims` - List all claims
- `GET /api/admin/claims/{claim_id}` - Get claim details
- `PATCH /api/admin/claims/{claim_id}/status` - Update claim status
- `GET /api/admin/stats` - Get system statistics

## Configuration

The application uses environment variables for configuration. Key settings:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `CORS_ORIGINS`: Allowed CORS origins
- `UPLOAD_DIR`: File upload directory
- `MAX_FILE_SIZE_MB`: Maximum file upload size
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

See `.env.example` for all available configuration options.

## Database Schema

### Users
- `id`: Primary key
- `email`: Unique email address
- `booking_reference`: Booking reference number
- `is_admin`: Admin flag
- `created_at`: Creation timestamp

### Claims
- `id`: Primary key
- `claim_id`: Unique claim identifier
- `user_id`: Foreign key to users
- `full_name`: User's full name
- `email`: User's email
- `booking_reference`: Booking reference
- `flight_number`: Flight number (format: XX1234)
- `planned_departure_date`: Scheduled departure date
- `actual_departure_time`: Actual departure time
- `status`: Claim status
- `created_at`: Creation timestamp

### Documents
- `id`: Primary key
- `claim_id`: Foreign key to claims
- `filename`: Stored filename
- `original_filename`: Original filename
- `file_size`: File size in bytes
- `mime_type`: MIME type
- `file_path`: File storage path
- `document_type`: Type of document

### Chat Sessions
- `id`: Primary key
- `session_id`: Unique session identifier
- `user_id`: Foreign key to users (optional)
- `created_at`: Creation timestamp

### Chat Messages
- `id`: Primary key
- `session_id`: Foreign key to chat sessions
- `message`: Message content
- `sender`: Sender type (user/bot)
- `created_at`: Creation timestamp

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
```

### Type Checking
```bash
mypy app/
```

### Linting
```bash
flake8 app/
```

## Deployment

### Docker
```bash
docker build -t flight-claim-api .
docker run -p 8000:8000 flight-claim-api
```

### Docker Compose
```bash
docker-compose up -d
```

### Production Considerations

1. **Environment Variables**: Set production values for all sensitive configuration
2. **Database**: Use managed PostgreSQL service with backups
3. **File Storage**: Consider using cloud storage (S3, GCS) for file uploads
4. **SSL/TLS**: Use HTTPS with proper certificates
5. **Monitoring**: Set up application monitoring and alerting
6. **Rate Limiting**: Configure appropriate rate limits
7. **Logging**: Configure centralized logging

## Security

- JWT-based authentication with configurable expiration
- Password hashing with bcrypt
- Input validation and sanitization
- SQL injection prevention through ORM
- File upload validation and type checking
- Rate limiting to prevent abuse
- CORS configuration for frontend security

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, email team@flightclaim.com or create an issue in the GitHub repository.