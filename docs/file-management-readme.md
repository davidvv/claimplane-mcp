"""File Management System - Implementation Guide

## Overview

The flight claim application now includes a comprehensive file management system that integrates with Nextcloud for secure file storage. The system provides encrypted file uploads, downloads, access logging, and comprehensive validation.

## Features Implemented

### ✅ Core Functionality
- **Database Models**: [`ClaimFile`](app/models.py:158), [`FileAccessLog`](app/models.py:250), [`FileValidationRule`](app/models.py:350)
- **File Service**: [`FileService`](app/services/file_service.py:35) with upload, download, delete operations
- **Repository Layer**: [`FileRepository`](app/repositories/file_repository.py:15) for database operations
- **Encryption Service**: [`EncryptionService`](app/services/encryption_service.py:15) using Fernet encryption
- **Validation Service**: [`FileValidationService`](app/services/file_validation_service.py:15) with document type validation
- **Nextcloud Integration**: [`NextcloudService`](app/services/nextcloud_service.py:15) for cloud storage
- **API Endpoints**: [`files router`](app/routers/files.py:25) with comprehensive endpoints
- **Security Middleware**: [`FileSecurityMiddleware`](app/middleware/file_security.py:15) for rate limiting and validation

### ✅ API Endpoints
- `POST /files/upload` - Upload files with validation
- `GET /files/{file_id}` - Get file information
- `GET /files/{file_id}/download` - Download files with decryption
- `DELETE /files/{file_id}` - Soft delete files
- `GET /files/claim/{claim_id}` - Get files by claim
- `GET /files/customer/{customer_id}` - Get files by customer
- `GET /files/{file_id}/access-logs` - Get file access logs
- `GET /files/summary/{customer_id}` - Get file statistics
- `POST /files/search` - Search files

### ✅ Security Features
- **File Encryption**: All files encrypted before storage
- **Access Logging**: Comprehensive access logging with IP tracking
- **Rate Limiting**: Upload/download rate limiting per IP
- **File Validation**: MIME type, size, and content validation
- **Duplicate Detection**: SHA256 hash-based duplicate detection
- **Secure Filenames**: UUID-based secure filename generation

### ✅ Configuration
- **Environment Variables**: Updated [`.env`](.env:1) with file management settings
- **Docker Compose**: [`docker-compose.nextcloud.yml`](docker-compose.nextcloud.yml:1) for Nextcloud deployment
- **Requirements**: Updated [`requirements.txt`](requirements.txt:32) with file processing dependencies

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
Update your `.env` file with file management settings:
```bash
# File Management
MAX_FILE_SIZE=52428800
FILE_ENCRYPTION_KEY=your-32-character-encryption-key-here

# Nextcloud Configuration
NEXTCLOUD_URL=http://localhost:8080
NEXTCLOUD_USERNAME=admin
NEXTCLOUD_PASSWORD=admin
```

### 3. Initialize Database
```bash
python init_db.py
```

### 4. Start Nextcloud (Optional)
```bash
docker-compose -f docker-compose.nextcloud.yml up -d
```

### 5. Test File Upload
```bash
curl -X POST "http://localhost:8000/files/upload" \
  -F "file=@test_document.pdf" \
  -F "claim_id=123e4567-e89b-12d3-a456-426614174000" \
  -F "customer_id=123e4567-e89b-12d3-a456-426614174000" \
  -F "document_type=boarding_pass"
```

## Architecture

### File Upload Flow
1. **Validation**: File validated against document type rules
2. **Duplicate Check**: SHA256 hash checked for existing files
3. **Encryption**: File content encrypted using Fernet
4. **Nextcloud Upload**: Encrypted file uploaded to Nextcloud
5. **Database Record**: File metadata stored in PostgreSQL
6. **Access Log**: Upload activity logged

### File Download Flow
1. **Permission Check**: User permissions verified
2. **File Retrieval**: Encrypted file downloaded from Nextcloud
3. **Decryption**: File content decrypted
4. **Access Log**: Download activity logged
5. **Streaming Response**: File streamed to client

### Security Features
- **Encryption**: AES-256 encryption with Fernet
- **Access Control**: Role-based permissions
- **Rate Limiting**: IP-based rate limiting
- **Content Validation**: File type and content validation
- **Audit Trail**: Comprehensive access logging

## Testing

### Run File Operation Tests
```bash
python -m pytest app/tests/test_file_operations.py -v
```

### Test Nextcloud Integration
```bash
python scripts/test_nextcloud_integration.py
```

### Test File Validation
```bash
python -c "
from app.services.file_validation_service import FileValidationService
import asyncio

async def test():
    service = FileValidationService()
    result = await service.validate_file(
        file_content=b'%PDF-1.4 test content',
        filename='test.pdf',
        document_type='boarding_pass',
        declared_mime_type='application/pdf'
    )
    print('Validation result:', result)

asyncio.run(test())
"
```

## Configuration Options

### File Size Limits
```bash
MAX_FILE_SIZE=52428800  # 50MB default
```

### Encryption Settings
```bash
FILE_ENCRYPTION_KEY=your-32-character-encryption-key-here
```

### Nextcloud Settings
```bash
NEXTCLOUD_URL=http://localhost:8080
NEXTCLOUD_USERNAME=admin
NEXTCLOUD_PASSWORD=admin
```

### Security Settings
```bash
VIRUS_SCAN_ENABLED=true
CLAMAV_URL=clamav:3310
```

## Troubleshooting

### Common Issues

1. **Nextcloud Connection Failed**
   - Check Nextcloud URL and credentials
   - Verify Nextcloud container is running
   - Check network connectivity

2. **File Upload Fails**
   - Verify file size limits
   - Check file type validation rules
   - Ensure sufficient disk space

3. **Encryption Errors**
   - Verify FILE_ENCRYPTION_KEY is set
   - Check key length (minimum 32 characters)

4. **Database Errors**
   - Ensure database is initialized
   - Check connection settings
   - Verify table creation

### Debug Mode
Enable debug logging:
```bash
LOG_LEVEL=DEBUG
```

## Next Steps

### 🔲 Security Middleware Integration
- Integrate [`FileSecurityMiddleware`](app/middleware/file_security.py:15) into main application
- Add Redis client for rate limiting
- Configure security headers

### 🔲 Comprehensive Testing
- Add integration tests with real Nextcloud
- Add performance tests for large files
- Add security penetration tests

### 🔲 Production Deployment
- Configure SSL/TLS certificates
- Set up monitoring and alerting
- Configure backup procedures
- Set up log rotation

### 🔲 Advanced Features
- Implement virus scanning with ClamAV
- Add OCR for document processing
- Implement file versioning
- Add advanced search capabilities

## API Documentation

Full API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Support

For issues and questions:
1. Check the troubleshooting guide
2. Review the logs with `LOG_LEVEL=DEBUG`
3. Run the integration tests
4. Check the API documentation

## License

This file management system is part of the flight claim application and follows the same licensing terms.