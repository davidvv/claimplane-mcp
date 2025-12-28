# EasyAirClaim - Flight Claim Management System

A sophisticated flight compensation claim processing platform built with FastAPI, featuring automated email notifications, admin dashboard, EU261/2004 compensation calculation, secure file storage with encryption, and seamless Nextcloud integration.

## 🚀 Key Features

### **Advanced File Management**
- **Secure File Upload/Download**: Multi-format file handling with streaming support for large files
- **Document Type Validation**: Specialized validation rules for boarding passes, ID documents, receipts, bank statements, and more
- **File Integrity Verification**: SHA256 hashing and content verification to prevent corruption
- **Access Control**: Granular permissions and file-level security controls
- **File Search & Organization**: Advanced search capabilities with metadata filtering
- **File Access Logging**: Comprehensive audit trails for compliance and security

### **Enterprise Security**
- **End-to-End Encryption**: Fernet encryption for all file content with secure key management
- **Content Security Scanning**: Malware detection, suspicious pattern analysis, and threat prevention
- **PDF Security Validation**: JavaScript detection, embedded file analysis, and page limit enforcement
- **Rate Limiting**: Configurable upload/download limits to prevent abuse
- **CORS Protection**: Configurable cross-origin resource sharing policies

### **Nextcloud Integration**
- **WebDAV Storage**: Seamless integration with Nextcloud for scalable file storage
- **Intelligent Retry Logic**: Exponential backoff and error classification for reliable operations
- **Upload Verification**: Automatic integrity checking after Nextcloud uploads
- **Chunked Uploads**: Memory-efficient handling of large files
- **Directory Management**: Automatic folder creation and path management

### **Flight Claim Processing**
- **Customer Management**: Registration and profile management for claim processing
- **Claim Tracking**: Comprehensive claim lifecycle management
- **Document Association**: Link files to specific claims and customers
- **Workflow Integration**: Support for claim processing workflows
- **Admin Dashboard**: Complete claim management with filtering, search, and bulk operations
- **Compensation Calculator**: Automatic EU261/2004 compensation calculation
- **Status Workflow**: Validated status transitions with complete audit trail

### **Automated Notifications** 🆕
- **Email Notifications**: Professional HTML email templates for all claim events
- **Async Processing**: Background email sending via Celery workers
- **Smart Retries**: Automatic retry with exponential backoff for failed emails
- **Claim Submitted**: Instant confirmation emails to customers
- **Status Updates**: Automated emails when claim status changes (approved, rejected, paid)
- **Document Review**: Re-upload request emails with clear instructions
- **Customizable**: Configurable SMTP settings and "From" address

## 📋 Development Status & Roadmap

**Current Status**: MVP Phase - Phase 2 Complete! 🎉

**Version**: v0.2.0

The platform now has a complete admin dashboard, automated email notifications, and async task processing.

### ✅ Phase 2 Complete (2025-10-30)
- Email notification system with 3 professional HTML templates
- Celery + Redis task queue for async processing
- Background email sending (non-blocking API)
- Gmail SMTP integration with custom "From" address
- Automatic retry logic for failed emails

📄 **See [PHASE2_SUMMARY.md](PHASE2_SUMMARY.md)** for implementation details
📖 **See [PHASE2_TESTING_GUIDE.md](PHASE2_TESTING_GUIDE.md)** for testing guide

### ✅ Phase 1 Complete (2025-10-29)
- Admin claim management with filtering and bulk operations
- EU261/2004 compensation calculation engine
- Document review and approval system
- Complete audit trail (status history, notes)
- 35 tests passing ✅

📄 **See [PHASE1_SUMMARY.md](PHASE1_SUMMARY.md)** for implementation details

📖 **See [ROADMAP.md](ROADMAP.md)** for the complete development plan

**Next Priority**:
- **Phase 3: Authentication & Authorization** - JWT authentication, user registration, role-based access control

For architecture details and development guidelines, see [CLAUDE.md](CLAUDE.md)

⚠️ **IMPORTANT**: Always use the `EasyAirClaim` conda environment. See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)

## 🛠 Tech Stack

### **Core Framework**
- **FastAPI**: Modern, async-first web framework for high-performance APIs
- **SQLAlchemy 2.0**: Async ORM with comprehensive database relationship support
- **PostgreSQL**: Robust relational database with JSON support
- **Pydantic v2**: Advanced data validation and serialization

### **Security & Encryption**
- **Cryptography**: Fernet encryption for secure file storage
- **Python-JOSE**: JWT token management for authentication
- **Passlib**: Secure password hashing with bcrypt
- **Libmagic**: Advanced file type detection and validation

### **Cloud Integration**
- **Nextcloud**: Enterprise file storage and sharing platform
- **WebDAV**: Standard protocol for file operations
- **HTTPX**: Async HTTP client for reliable external API calls

### **Infrastructure & DevOps**
- **Docker**: Containerized deployment with multi-stage builds
- **Nginx**: High-performance reverse proxy and load balancer
- **Redis**: Message broker for Celery and caching
- **PostgreSQL**: Primary data storage with health checks
- **Celery**: Distributed task queue for async processing
- **aiosmtplib**: Async SMTP client for email notifications

### **Development & Testing**
- **Pytest**: Comprehensive testing framework with async support
- **Uvicorn**: ASGI server for development and production
- **Alembic**: Database migration management

## 📁 Project Structure

```
flight_claim/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application with lifespan management
│   ├── config.py                  # Configuration management
│   ├── database.py                # Async database connection handling
│   ├── models.py                  # SQLAlchemy models (Customer, Claim, File, etc.)
│   ├── schemas/                   # Pydantic schemas for API contracts
│   │   ├── __init__.py
│   │   └── file_schemas.py         # File-specific data models
│   ├── middleware/                # Advanced middleware components
│   │   ├── __init__.py
│   │   └── file_security.py       # File security and validation middleware
│   ├── repositories/              # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py                # Generic repository base class
│   │   ├── customer_repository.py # Customer data operations
│   │   ├── claim_repository.py    # Claim data operations
│   │   └── file_repository.py     # File data operations
│   ├── routers/                   # API route handlers
│   │   ├── __init__.py
│   │   ├── customers.py           # Customer management endpoints
│   │   ├── claims.py             # Claim processing endpoints
│   │   ├── files.py              # File management endpoints
│   │   └── health.py             # System health monitoring
│   ├── services/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── encryption_service.py  # File encryption/decryption
│   │   ├── file_service.py       # File operations and management
│   │   ├── file_validation_service.py # Security and content validation
│   │   └── nextcloud_service.py  # Nextcloud WebDAV integration
│   ├── exceptions.py             # Custom exception hierarchy
│   └── middleware.py             # Global middleware setup
├── API/
│   └── openapi.yaml              # OpenAPI specification
├── docs/                         # Comprehensive documentation
│   ├── api-reference.md
│   ├── security-best-practices.md
│   └── file-management-implementation-guide.md
├── scripts/                      # Utility and setup scripts
│   ├── generate_secrets.py       # Secure key generation
│   ├── setup_nextcloud.sh        # Nextcloud integration setup
│   └── init_file_validation_rules.py
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Multi-stage container build
├── docker-compose.yml            # Main application stack
├── docker-compose.nextcloud.yml  # Nextcloud integration stack
├── nginx.conf                    # Reverse proxy configuration
└── docker-secrets.example.txt    # Secrets management template
```

## 🚀 Quick Start

## ⚡ Development vs Production Setup

### **Two Modes of Operation**

This project supports two different frontend serving modes. Choose based on your use case:

#### 🔧 **Development Mode** (Recommended for Active Development)

**Port:** `3000` (Vite Dev Server)

**Use when:**
- Making frequent frontend changes
- Need hot module reload (instant updates)
- Active development work

**Setup:**
```bash
# Start Docker services (backend, database, Redis)
docker-compose up -d

# Start Vite dev server
cd frontend_Claude45
npm run dev
```

**Access:** http://localhost:3000 (or http://192.168.5.209:3000 for network access)

**Cloudflare Tunnel:** Point to `http://192.168.5.209:3000`

**Benefits:**
- ⚡ **Instant feedback** - Changes reflect in < 1 second
- 🔥 **Hot Module Reload** - No page refresh needed
- 🐛 **Better debugging** - Source maps and dev tools
- 🚀 **Fast iteration** - No build step required

---

#### 🚢 **Production Mode** (Testing Production Builds)

**Port:** `80` (nginx serving built frontend)

**Use when:**
- Testing production builds before deployment
- Verifying optimized bundle works correctly
- Final testing before going live

**Setup:**
```bash
# Build frontend
cd frontend_Claude45
npm run build

# Restart nginx to serve new build
cd ..
docker-compose restart nginx
```

**Access:** http://localhost (or http://192.168.5.209 for network access)

**Cloudflare Tunnel:** Point to `http://192.168.5.209:80`

**Benefits:**
- 📦 **Optimized bundle** - Minified and tree-shaken
- 🎯 **Production-like** - Same setup as deployment
- ✅ **Final verification** - Test exactly what users will see

---

### **Quick Reference Table**

| Aspect | Development (Port 3000) | Production (Port 80) |
|--------|------------------------|---------------------|
| **Server** | Vite dev server | nginx |
| **Start Command** | `npm run dev` | `npm run build` + restart nginx |
| **Hot Reload** | ✅ Yes | ❌ No |
| **Speed** | ⚡ Instant | 🐌 ~10s rebuild |
| **Debugging** | ✅ Easy | ⚠️ Harder |
| **Use For** | Daily development | Pre-deployment testing |
| **Cloudflare Tunnel** | `:3000` | `:80` |

---

### **Switching Between Modes**

**From Production → Development:**
```bash
# Start Vite dev server
cd frontend_Claude45
npm run dev

# Update Cloudflare tunnel to port 3000
```

**From Development → Production:**
```bash
# Build frontend
cd frontend_Claude45
npm run build

# Restart nginx
cd ..
docker-compose restart nginx

# Update Cloudflare tunnel to port 80
```

---

### Prerequisites

- **Docker and Docker Compose** (recommended for full stack)
- **Python 3.11+** (for local development)
- **Node.js 18+** (for frontend development)
- **Nextcloud instance** (optional, for file storage)

### Complete Docker Stack (Recommended)

1. **Clone and configure**:
   ```bash
   # The project is already set up in your current directory
   # Copy and configure environment variables
   cp docker-secrets.example.txt .env
   # Edit .env with your configuration
   ```

2. **Start the complete stack**:
   ```bash
   # Start Nextcloud services first
   docker-compose -f docker-compose.nextcloud.yml up -d

   # Start the main application stack
   docker-compose up -d
   ```

3. **Verify deployment**:
   ```bash
   # Check API health
   curl http://localhost:8000/health

   # Check Nextcloud status
   curl http://localhost:8081/status.php

   # Access interactive API documentation
   open http://localhost:8000/docs

   # Access Nextcloud web interface
   open http://localhost:8081
   ```

### File Management Testing

1. **Upload a test file**:
   ```bash
   curl -X POST "http://localhost:8000/files/upload" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test.pdf" \
     -F "claim_id=test-claim-123" \
     -F "customer_id=test-customer-456" \
     -F "document_type=boarding_pass"
   ```

2. **Download a file**:
   ```bash
   curl "http://localhost:8000/files/{file_id}/download" \
     -H "X-Customer-ID: test-customer-456" \
     -o downloaded_file.pdf
   ```

### Local Development Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup PostgreSQL**:
   ```bash
   # Using Docker for database
   docker run -d \
     --name flight_claim_db \
     -e POSTGRES_DB=flight_claim \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=postgres \
     -p 5432:5432 \
     postgres:15-alpine
   ```

3. **Configure environment**:
   ```bash
   cp docker-secrets.example.txt .env
   # Edit .env file with local configuration
   ```

4. **Run the application**:
   ```bash
   python app/main.py
   ```

5. **Access points**:
   - **API Documentation**: http://localhost:8000/docs
   - **API Base**: http://localhost:8000
   - **Health Check**: http://localhost:8000/health
   - **File Operations**: http://localhost:8000/files/*

## 📋 API Endpoints

### **File Management**
- `POST /files/upload` - Upload file with validation and encryption
- `GET /files/{file_id}` - Get file information and metadata
- `GET /files/{file_id}/download` - Download file with access control
- `DELETE /files/{file_id}` - Soft delete file
- `GET /files/claim/{claim_id}` - List files for a specific claim
- `GET /files/customer/{customer_id}` - List files for a customer
- `GET /files/{file_id}/access-logs` - Get file access history
- `GET /files/summary/{customer_id}` - Get file statistics summary
- `POST /files/search` - Advanced file search with filters
- `GET /files/validation-rules` - Get document validation rules

### **Customer Management**
- `POST /customers` - Create new customer
- `GET /customers/{customer_id}` - Get customer by ID
- `GET /customers` - List customers (paginated)
- `GET /customers/search/by-email/{email}` - Search customers by email
- `GET /customers/search/by-name/{name}` - Search customers by name

### **Claim Processing**
- `POST /claims` - Create claim for existing customer
- `POST /claims/submit` - Submit claim with customer info
- `GET /claims/{claim_id}` - Get claim by ID
- `GET /claims` - List claims (with optional filtering)
- `GET /claims/customer/{customer_id}` - Get claims for customer
- `GET /claims/status/{status}` - Get claims by status

### **System Health**
- `GET /health` - Basic health check
- `GET /health/db` - Database connectivity check
- `GET /health/detailed` - Comprehensive system health
- `GET /` - API information
- `GET /info` - Detailed API and feature information

## 🔒 Security Features

### **File Encryption**
- **Fernet Encryption**: Industry-standard symmetric encryption for all file content
- **Secure Key Management**: Environment-based key configuration with validation
- **Integrity Verification**: SHA256 hashing to ensure file content hasn't been tampered with
- **Streaming Encryption**: Memory-efficient encryption for large files

### **Content Validation**
- **MIME Type Detection**: Advanced file type detection using libmagic
- **Document-Specific Rules**: Tailored validation rules for different document types:
  - Boarding passes (PDF, JPEG, PNG)
  - ID documents (PDF, JPEG, PNG)
  - Bank statements (PDF only)
  - Flight tickets (PDF, JPEG, PNG)
  - Receipts and invoices (PDF, JPEG, PNG)
- **Security Scanning**: Automated detection of suspicious patterns and potential malware
- **PDF Content Analysis**: JavaScript detection, embedded file analysis, and page validation

### **Access Control**
- **File-Level Permissions**: Granular access control for files based on ownership
- **Audit Logging**: Comprehensive logging of all file access and operations
- **Rate Limiting**: Configurable limits to prevent abuse and ensure fair usage
- **CORS Protection**: Secure cross-origin resource sharing configuration

## ☁️ Nextcloud Integration

### **WebDAV Storage**
- **Seamless Integration**: Full WebDAV protocol support for file operations
- **Intelligent Error Handling**: Sophisticated error classification and recovery
- **Retry Logic**: Exponential backoff with jitter for reliable operations
- **Connection Pooling**: Efficient HTTP connection management

### **Advanced Features**
- **Upload Verification**: Automatic integrity checking after file uploads
- **Chunked Uploads**: Memory-efficient handling of large files
- **Directory Management**: Automatic folder creation and path management
- **Share Link Creation**: Generate secure share links for file access
- **File Metadata**: Retrieve comprehensive file information and properties

### **Configuration**
```yaml
# docker-compose.yml Nextcloud integration
NEXTCLOUD_URL: http://nextcloud:80
NEXTCLOUD_USERNAME: admin
NEXTCLOUD_PASSWORD: secure_password
NEXTCLOUD_TIMEOUT: 30
NEXTCLOUD_MAX_RETRIES: 3
```

## 🆕 Recent Updates & Improvements

### **File Corruption Fixes**
- **Root Cause Resolution**: Fixed underlying issues causing file corruption during upload/download
- **Enhanced Error Handling**: Improved error classification and recovery mechanisms
- **Integrity Verification**: Added comprehensive file integrity checking
- **Streaming Improvements**: Better memory management for large file operations

### **Performance Enhancements**
- **Async Operations**: Full async/await implementation for better performance
- **Connection Optimization**: Improved HTTP connection handling and pooling
- **Memory Efficiency**: Streaming support for large file operations
- **Caching Strategy**: Redis integration for improved response times

### **Security Improvements**
- **Enhanced Validation**: More comprehensive file content validation
- **Security Scanning**: Advanced malware and threat detection
- **Encryption Upgrades**: Improved key management and encryption processes
- **Access Logging**: Detailed audit trails for compliance

### **API Enhancements**
- **File Search**: Advanced search capabilities with multiple filters
- **Batch Operations**: Support for bulk file operations
- **Real-time Validation**: Immediate feedback on file uploads
- **Progress Tracking**: Upload/download progress monitoring

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Basic functionality tests
python test_api.py

# File operation tests
python app/tests/test_file_operations.py

# Nextcloud integration tests
python scripts/test_nextcloud_integration.py

# Security and validation tests
python app/tests/test_edge_cases.py
```

### **Test Coverage**
- ✅ File upload/download operations
- ✅ Nextcloud WebDAV integration
- ✅ File validation and security scanning
- ✅ Encryption/decryption processes
- ✅ Error handling and recovery
- ✅ Performance and load testing

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

## ⚙️ Configuration

### **Environment Variables**

Create a `.env` file based on `docker-secrets.example.txt`:

```bash
# Application Configuration
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/flight_claim
SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO

# File Management
FILE_ENCRYPTION_KEY=your-file-encryption-key-here
MAX_FILE_SIZE=52428800
CHUNK_SIZE=8192
UPLOAD_VERIFICATION_ENABLED=true

# Nextcloud Integration
NEXTCLOUD_URL=http://nextcloud:80
NEXTCLOUD_USERNAME=admin
NEXTCLOUD_PASSWORD=your-nextcloud-password
NEXTCLOUD_TIMEOUT=30
NEXTCLOUD_MAX_RETRIES=3

# Security & Performance
RATE_LIMIT_UPLOAD=100/minute
RATE_LIMIT_DOWNLOAD=1000/minute
VIRUS_SCAN_ENABLED=false
CLAMAV_URL=clamav:3310

# API Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8081
API_VERSION=1.0.0
API_TITLE=Flight Claim System API
```

### **File Validation Rules**

The system includes predefined validation rules for different document types:

| Document Type | Max Size | Allowed Types | Security Scan | Encryption |
|---------------|----------|---------------|---------------|------------|
| Boarding Pass | 10MB | PDF, JPEG, PNG | ✅ | ✅ |
| ID Document | 5MB | PDF, JPEG, PNG | ✅ | ✅ |
| Bank Statement | 5MB | PDF | ✅ | ✅ |
| Flight Ticket | 5MB | PDF, JPEG, PNG | ✅ | ✅ |
| Receipt | 2MB | PDF, JPEG, PNG | ✅ | ✅ |

## 🛠 Development

### **Adding New Features**

1. **Models**: Add SQLAlchemy models in `app/models.py`
2. **Schemas**: Create Pydantic schemas in `app/schemas/`
3. **Services**: Implement business logic in `app/services/`
4. **Repositories**: Add data access layer in `app/repositories/`
5. **Routers**: Create API endpoints in `app/routers/`
6. **Tests**: Add comprehensive tests in `app/tests/`

### **File Management Development**

For file-related features:

```python
# Example: Adding a new document type
# 1. Update validation service
file_validation_service.default_rules["new_document_type"] = {
    "max_file_size": 5 * 1024 * 1024,
    "allowed_mime_types": ["application/pdf"],
    "required_extensions": [".pdf"],
    "requires_scan": True,
    "requires_encryption": True
}

# 2. Add to file schemas if needed
# 3. Update API documentation
```

### **Database Migrations**

For production deployments:

```bash
# Install Alembic if not already included
pip install alembic

# Initialize migrations (if not done already)
alembic init alembic

# Create new migration
alembic revision --autogenerate -m "Add file management tables"

# Apply migrations
alembic upgrade head

# Rollback (if needed)
alembic downgrade -1
```

## 🚢 Production Deployment

### **Security Hardening**
- **CORS Configuration**: Restrict origins to trusted domains only
- **HTTPS Enforcement**: Configure Nginx for SSL/TLS termination
- **Authentication**: Implement JWT-based authentication
- **Rate Limiting**: Enable strict rate limiting for production
- **Security Headers**: Enable security headers middleware

### **Infrastructure Setup**
- **Managed Database**: Use services like AWS RDS, Google Cloud SQL, or Azure Database
- **Load Balancing**: Configure Nginx or cloud load balancers
- **Monitoring**: Implement logging, metrics collection, and alerting
- **Backups**: Automated database and file backup strategies
- **High Availability**: Multi-zone deployment configuration

### **Nextcloud Production Setup**
- **Separate Database**: Use dedicated PostgreSQL instance for Nextcloud
- **Redis Clustering**: Configure Redis cluster for session management
- **Storage Backend**: Configure object storage (S3, GCS, etc.)
- **SSL Certificates**: Proper SSL/TLS configuration
- **Monitoring**: Nextcloud-specific monitoring and alerting

### **Scaling Considerations**
- **Horizontal Scaling**: Multiple API instances behind load balancer
- **File Storage**: Distributed file storage with Nextcloud
- **Database Scaling**: Read replicas and connection pooling
- **Caching Strategy**: Redis cluster for improved performance

## 🤝 Contributing

We welcome contributions to improve the file management platform:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes with comprehensive tests
4. **Test** thoroughly, especially file operations and security features
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to the branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### **Development Guidelines**
- Follow PEP 8 style guidelines
- Add tests for all new functionality
- Update documentation for API changes
- Ensure file security features are maintained
- Test with various file types and sizes

### **File Management Contributions**
When contributing file-related features:
- Consider security implications
- Test with edge cases (large files, special characters, etc.)
- Ensure Nextcloud compatibility
- Update validation rules if adding new document types
- Add appropriate error handling

## 📄 License

Private - All rights reserved.

## 🆘 Support & Contact

For support and inquiries, contact: **easyairclaim@gmail.com**

### **Getting Help**
- 📖 **Documentation**: Check the `/docs` folder for detailed guides
- 🔧 **Troubleshooting**: See `docs/troubleshooting-guide.md`
- 🚨 **Issues**: Report bugs and feature requests on the repository
- 💬 **Discussions**: Use repository discussions for questions and ideas

### **Professional Services**
- Custom file validation rules
- Nextcloud integration setup
- Security hardening
- Performance optimization
- Training and documentation

---

## 📊 Key Metrics

| Feature | Status | Description |
|---------|--------|-------------|
| File Upload | ✅ Production | Multi-format with validation |
| File Download | ✅ Production | Streaming with access control |
| Nextcloud Integration | ✅ Production | WebDAV with retry logic |
| File Encryption | ✅ Production | Fernet encryption |
| Security Scanning | ✅ Production | Malware detection |
| Access Logging | ✅ Production | Comprehensive audit trails |
| API Documentation | ✅ Production | Interactive OpenAPI docs |
| Docker Deployment | ✅ Production | Complete containerized stack |
| Testing Suite | ✅ Production | Comprehensive test coverage |

**Built with ❤️ for secure and reliable file management**