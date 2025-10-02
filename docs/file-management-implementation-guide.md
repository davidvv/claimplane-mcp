# File Management System - Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the comprehensive file management system designed for the flight claim application. The system integrates with Nextcloud for secure file storage and includes robust security, access control, and validation mechanisms.

## Prerequisites

### System Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+
- PostgreSQL 15+
- Redis 7+
- Python 3.11+
- 8GB+ RAM, 4+ CPU cores
- 100GB+ available storage

### Network Requirements
- Internet access for Docker images
- SSL/TLS certificates for production
- Domain name for Nextcloud instance
- Firewall configuration for required ports

## Phase 1: Infrastructure Setup (Week 1)

### 1.1 Environment Preparation

```bash
# Create project directory structure
mkdir -p flight-claim-file-management/{app,config,scripts,volumes,logs}
cd flight-claim-file-management

# Create environment files
cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/flight_claim
POSTGRES_DB=flight_claim
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Nextcloud Configuration
NEXTCLOUD_DOMAIN=nextcloud.yourdomain.com
NEXTCLOUD_ADMIN_USER=admin
NEXTCLOUD_ADMIN_PASSWORD=your_secure_admin_password
NEXTCLOUD_DB_PASSWORD=your_secure_db_password
NEXTCLOUD_REDIS_PASSWORD=your_secure_redis_password

# Security Configuration
FILE_ENCRYPTION_KEY=your_32_character_encryption_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
API_KEY_SECRET=your_api_key_secret_here

# File Processing Configuration
MAX_FILE_SIZE=52428800
FILE_UPLOAD_TIMEOUT=300
VIRUS_SCAN_ENABLED=true
CLAMAV_URL=clamav:3310

# Performance Configuration
WORKER_PROCESSES=4
CACHE_TTL=3600
CONNECTION_POOL_SIZE=20

# Monitoring Configuration
LOG_LEVEL=INFO
METRICS_ENABLED=true
ALERTING_ENABLED=true
EOF

# Create Docker network
docker network create file_management_network
```

### 1.2 Database Setup

```sql
-- init-scripts/01-file-management-tables.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create file management schema
CREATE SCHEMA IF NOT EXISTS file_management;

-- Create claim_files table
CREATE TABLE claim_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    
    -- File metadata
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    
    -- Document classification
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN (
        'boarding_pass', 'id_document', 'receipt', 'bank_statement', 
        'flight_ticket', 'delay_certificate', 'cancellation_notice', 'other'
    )),
    
    -- Storage information
    storage_provider VARCHAR(50) DEFAULT 'nextcloud',
    storage_path TEXT NOT NULL,
    nextcloud_file_id VARCHAR(255),
    nextcloud_share_token VARCHAR(255),
    
    -- Security and access
    encryption_status VARCHAR(20) DEFAULT 'encrypted' CHECK (encryption_status IN ('encrypted', 'decrypted', 'pending')),
    access_level VARCHAR(20) DEFAULT 'private' CHECK (access_level IN ('public', 'private', 'restricted')),
    download_count INTEGER DEFAULT 0,
    
    -- Status and workflow
    status VARCHAR(50) DEFAULT 'uploaded' CHECK (status IN (
        'uploaded', 'scanning', 'validated', 'rejected', 'approved', 'archived'
    )),
    validation_status VARCHAR(50) DEFAULT 'pending',
    rejection_reason TEXT,
    
    -- Audit trail
    uploaded_by UUID REFERENCES customers(id),
    reviewed_by UUID REFERENCES customers(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Soft delete and versioning
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    version INTEGER DEFAULT 1,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_claim_files_claim_id ON claim_files(claim_id);
CREATE INDEX idx_claim_files_customer_id ON claim_files(customer_id);
CREATE INDEX idx_claim_files_status ON claim_files(status);
CREATE INDEX idx_claim_files_document_type ON claim_files(document_type);
CREATE INDEX idx_claim_files_file_hash ON claim_files(file_hash);
CREATE INDEX idx_claim_files_uploaded_at ON claim_files(uploaded_at);
CREATE INDEX idx_claim_files_expires_at ON claim_files(expires_at) WHERE expires_at IS NOT NULL;

-- Create file access logs table
CREATE TABLE file_access_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES claim_files(id) ON DELETE CASCADE,
    user_id UUID REFERENCES customers(id),
    access_type VARCHAR(50) NOT NULL CHECK (access_type IN (
        'upload', 'download', 'view', 'share', 'delete', 'restore', 'update'
    )),
    ip_address INET,
    user_agent TEXT,
    referrer TEXT,
    access_status VARCHAR(20) NOT NULL CHECK (access_status IN ('success', 'denied', 'error')),
    failure_reason TEXT,
    session_id VARCHAR(255),
    access_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Geographic information for security monitoring
    country_code VARCHAR(2),
    city VARCHAR(100),
    coordinates POINT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for access logs
CREATE INDEX idx_file_access_logs_file_id ON file_access_logs(file_id);
CREATE INDEX idx_file_access_logs_user_id ON file_access_logs(user_id);
CREATE INDEX idx_file_access_logs_access_time ON file_access_logs(access_time);
CREATE INDEX idx_file_access_logs_ip_address ON file_access_logs(ip_address);

-- Create file validation rules
CREATE TABLE file_validation_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_type VARCHAR(50) NOT NULL,
    max_file_size BIGINT NOT NULL,
    allowed_mime_types TEXT[] NOT NULL,
    required_file_extensions TEXT[],
    
    -- Content validation rules
    min_dimensions VARCHAR(20),
    max_dimensions VARCHAR(20),
    max_pages INTEGER,
    requires_ocr BOOLEAN DEFAULT FALSE,
    allowed_content_patterns TEXT[],
    
    -- Security requirements
    requires_scan BOOLEAN DEFAULT TRUE,
    requires_encryption BOOLEAN DEFAULT TRUE,
    retention_days INTEGER,
    
    -- Status and priority
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 100,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default validation rules
INSERT INTO file_validation_rules (
    document_type, max_file_size, allowed_mime_types, 
    required_file_extensions, max_pages, requires_scan
) VALUES
('boarding_pass', 5242880, ARRAY['application/pdf', 'image/jpeg', 'image/png'], ARRAY['.pdf', '.jpg', '.jpeg', '.png'], 2, TRUE),
('id_document', 10485760, ARRAY['application/pdf', 'image/jpeg', 'image/png'], ARRAY['.pdf', '.jpg', '.jpeg', '.png'], 2, TRUE),
('receipt', 2097152, ARRAY['application/pdf', 'image/jpeg', 'image/png'], ARRAY['.pdf', '.jpg', '.jpeg', '.png'], 5, TRUE),
('bank_statement', 10485760, ARRAY['application/pdf'], ARRAY['.pdf'], 10, TRUE);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER update_claim_files_updated_at BEFORE UPDATE ON claim_files
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_file_validation_rules_updated_at BEFORE UPDATE ON file_validation_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 1.3 Nextcloud Configuration

```bash
# Create Nextcloud configuration directory
mkdir -p config/nextcloud

# Create Nextcloud configuration
cat > config/nextcloud/config.php << 'EOF'
<?php
$CONFIG = array (
  'instanceid' => 'oc1234567890',
  'passwordsalt' => 'your_password_salt_here',
  'secret' => 'your_secret_key_here',
  'trusted_domains' => 
  array (
    0 => 'nextcloud.yourdomain.com',
    1 => 'localhost',
    2 => '127.0.0.1',
  ),
  'datadirectory' => '/var/www/html/data',
  'dbtype' => 'pgsql',
  'version' => '27.1.0.0',
  'overwrite.cli.url' => 'https://nextcloud.yourdomain.com',
  'dbname' => 'nextcloud',
  'dbhost' => 'nextcloud-db',
  'dbport' => '',
  'dbtableprefix' => 'oc_',
  'dbuser' => 'nextcloud',
  'dbpassword' => '${NEXTCLOUD_DB_PASSWORD}',
  'installed' => true,
  'memcache.local' => '\\OC\\Memcache\\Redis',
  'memcache.distributed' => '\\OC\\Memcache\\Redis',
  'memcache.locking' => '\\OC\\Memcache\\Redis',
  'redis' => 
  array (
    'host' => 'nextcloud-redis',
    'password' => '${NEXTCLOUD_REDIS_PASSWORD}',
    'port' => 6379,
  ),
  'mail_smtpmode' => 'smtp',
  'mail_smtphost' => 'smtp.yourdomain.com',
  'mail_smtpport' => '587',
  'mail_smtpsecure' => 'tls',
  'mail_smtpauth' => true,
  'mail_smtpauthtype' => 'LOGIN',
  'mail_smtpname' => 'noreply@yourdomain.com',
  'mail_smtppassword' => 'your_email_password',
  'mail_from_address' => 'noreply',
  'mail_domain' => 'yourdomain.com',
  'maintenance' => false,
  'theme' => '',
  'loglevel' => 2,
  'updater.release.channel' => 'stable',
  'encryption.legacy_format_support' => false,
  'encryption.key_storage_migrated' => false,
  'filelocking.enabled' => true,
  'filelocking.ttl' => 3600,
  'trusted_proxies' => 
  array (
    0 => 'traefik',
    1 => '172.20.0.0/16',
  ),
  'forwarded_for_headers' => 
  array (
    0 => 'HTTP_X_FORWARDED_FOR',
    1 => 'HTTP_X_REAL_IP',
  ),
);
EOF
```

## Phase 2: Application Development (Weeks 2-3)

### 2.1 File Service Implementation

```python
# app/services/file_service.py
import asyncio
import aiofiles
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from uuid import UUID, uuid4
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models import claim_files, Claim, Customer
from app.services.nextcloud_service import NextcloudService
from app.services.file_validation_service import FileValidationService
from app.services.encryption_service import EncryptionService

logger = structlog.get_logger(__name__)

class FileService:
    """Core service for file management operations."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.validation_service = FileValidationService()
        self.encryption_service = EncryptionService()
        
    async def upload_file(self, file_content: bytes, filename: str, 
                         claim_id: UUID, customer_id: UUID, 
                         document_type: str, mime_type: str,
                         expires_in_days: Optional[int] = None) -> Dict:
        """
        Upload and process a new file.
        
        Args:
            file_content: Raw file content
            filename: Original filename
            claim_id: Associated claim ID
            customer_id: Owner customer ID
            document_type: Type of document
            mime_type: MIME type of the file
            expires_in_days: Optional expiration period
            
        Returns:
            Dictionary with upload results and file metadata
        """
        try:
            # Validate file
            validation_result = await self.validation_service.validate_file(
                file_content, filename, document_type
            )
            
            if not validation_result['is_valid']:
                raise ValueError(f"File validation failed: {validation_result['errors']}")
                
            # Calculate file hash
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Check for duplicate files
            existing_file = await self._get_file_by_hash(file_hash)
            if existing_file:
                logger.info(f"Duplicate file detected: {existing_file.id}")
                return {
                    'file_id': existing_file.id,
                    'status': 'duplicate',
                    'message': 'File already exists',
                    'existing_file_id': existing_file.id
                }
                
            # Encrypt file content
            encrypted_content = self.encryption_service.encrypt(file_content)
            
            # Generate unique filename
            unique_filename = f"{uuid4()}_{filename}"
            storage_path = f"claims/{claim_id}/{unique_filename}"
            
            # Upload to Nextcloud
            async with NextcloudService(
                base_url=os.getenv('NEXTCLOUD_URL'),
                username=os.getenv('NEXTCLOUD_USERNAME'),
                password=os.getenv('NEXTCLOUD_PASSWORD')
            ) as nc_service:
                
                upload_result = await nc_service.upload_file(
                    storage_path, encrypted_content, create_share=True
                )
                
            # Calculate expiration date
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
                
            # Create database record
            file_record = claim_files(
                id=uuid4(),
                claim_id=claim_id,
                customer_id=customer_id,
                filename=unique_filename,
                original_filename=filename,
                file_size=len(file_content),
                mime_type=mime_type,
                file_hash=file_hash,
                document_type=document_type,
                storage_provider='nextcloud',
                storage_path=storage_path,
                nextcloud_file_id=upload_result.get('file_id'),
                nextcloud_share_token=upload_result.get('share_token'),
                encryption_status='encrypted',
                access_level='private',
                status='uploaded',
                validation_status='validated',
                uploaded_by=customer_id,
                uploaded_at=datetime.utcnow(),
                expires_at=expires_at
            )
            
            self.db.add(file_record)
            await self.db.flush()
            
            # Schedule file processing tasks
            await self._schedule_file_processing(file_record.id)
            
            logger.info(
                f"File uploaded successfully",
                file_id=file_record.id,
                claim_id=claim_id,
                customer_id=customer_id,
                file_size=len(file_content)
            )
            
            return {
                'file_id': file_record.id,
                'status': 'uploaded',
                'filename': filename,
                'file_size': len(file_content),
                'mime_type': mime_type,
                'document_type': document_type,
                'uploaded_at': file_record.uploaded_at,
                'share_url': upload_result.get('share_url'),
                'validation_warnings': validation_result.get('warnings', [])
            }
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise
            
    async def download_file(self, file_id: UUID) -> bytes:
        """
        Download and decrypt a file.
        
        Args:
            file_id: UUID of the file to download
            
        Returns:
            Decrypted file content as bytes
        """
        file_record = await self.db.get(claim_files, file_id)
        if not file_record:
            raise ValueError(f"File {file_id} not found")
            
        if file_record.is_deleted:
            raise ValueError(f"File {file_id} has been deleted")
            
        if file_record.expires_at and file_record.expires_at < datetime.utcnow():
            raise ValueError(f"File {file_id} has expired")
            
        # Download from Nextcloud
        async with NextcloudService(
            base_url=os.getenv('NEXTCLOUD_URL'),
            username=os.getenv('NEXTCLOUD_USERNAME'),
            password=os.getenv('NEXTCLOUD_PASSWORD')
        ) as nc_service:
            
            encrypted_content = await nc_service.download_file(file_record.storage_path)
            
        # Decrypt content
        decrypted_content = self.encryption_service.decrypt(encrypted_content)
        
        # Update download count
        file_record.download_count += 1
        await self.db.flush()
        
        return decrypted_content
        
    async def delete_file(self, file_id: UUID, user_id: UUID) -> bool:
        """
        Soft delete a file (mark as deleted).
        
        Args:
            file_id: UUID of the file to delete
            user_id: ID of user performing the deletion
            
        Returns:
            True if deletion was successful
        """
        file_record = await self.db.get(claim_files, file_id)
        if not file_record:
            raise ValueError(f"File {file_id} not found")
            
        # Check if user has permission to delete
        if file_record.customer_id != user_id:
            # Check for admin or special permissions
            has_permission = await self._check_delete_permission(user_id, file_id)
            if not has_permission:
                raise PermissionError("User does not have permission to delete this file")
                
        # Soft delete
        file_record.is_deleted = True
        file_record.deleted_at = datetime.utcnow()
        
        # Optionally delete from Nextcloud (or keep for audit)
        if os.getenv('DELETE_FROM_STORAGE', 'false').lower() == 'true':
            async with NextcloudService(
                base_url=os.getenv('NEXTCLOUD_URL'),
                username=os.getenv('NEXTCLOUD_USERNAME'),
                password=os.getenv('NEXTCLOUD_PASSWORD')
            ) as nc_service:
                
                await nc_service.delete_file(file_record.storage_path)
                
        await self.db.flush()
        
        logger.info(
            f"File deleted successfully",
            file_id=file_id,
            user_id=user_id
        )
        
        return True
        
    async def get_file_info(self, file_id: UUID) -> Optional[Dict]:
        """Get comprehensive file information."""
        file_record = await self.db.get(claim_files, file_id)
        if not file_record:
            return None
            
        return {
            'id': file_record.id,
            'claim_id': file_record.claim_id,
            'customer_id': file_record.customer_id,
            'filename': file_record.original_filename,
            'file_size': file_record.file_size,
            'mime_type': file_record.mime_type,
            'document_type': file_record.document_type,
            'status': file_record.status,
            'uploaded_at': file_record.uploaded_at,
            'expires_at': file_record.expires_at,
            'download_count': file_record.download_count,
            'encryption_status': file_record.encryption_status,
            'storage_provider': file_record.storage_provider,
            'validation_status': file_record.validation_status,
            'is_deleted': file_record.is_deleted
        }
        
    async def _get_file_by_hash(self, file_hash: str) -> Optional[claim_files]:
        """Check if a file with the same hash already exists."""
        stmt = select(claim_files).where(
            and_(
                claim_files.file_hash == file_hash,
                claim_files.is_deleted == False
            )
        ).limit(1)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def _check_delete_permission(self, user_id: UUID, file_id: UUID) -> bool:
        """Check if user has permission to delete the file."""
        # Implement permission checking logic
        # This could check for admin roles, claim ownership, etc.
        return False
        
    async def _schedule_file_processing(self, file_id: UUID):
        """Schedule background processing tasks for the file."""
        # This would integrate with a task queue like Celery
        # Tasks could include: virus scanning, OCR, content analysis, etc.
        pass
```

### 2.2 File Repository Implementation

```python
# app/repositories/file_repository.py
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models import claim_files
from app.repositories.base import BaseRepository

class FileRepository(BaseRepository[claim_files]):
    """Repository for file management operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(claim_files, session)
        
    async def get_files_by_claim(self, claim_id: UUID, 
                               include_deleted: bool = False) -> List[claim_files]:
        """Get all files for a specific claim."""
        stmt = select(claim_files).where(claim_files.claim_id == claim_id)
        
        if not include_deleted:
            stmt = stmt.where(claim_files.is_deleted == False)
            
        result = await self.session.execute(stmt)
        return result.scalars().all()
        
    async def get_files_by_customer(self, customer_id: UUID, 
                                  include_deleted: bool = False) -> List[claim_files]:
        """Get all files owned by a customer."""
        stmt = select(claim_files).where(claim_files.customer_id == customer_id)
        
        if not include_deleted:
            stmt = stmt.where(claim_files.is_deleted == False)
            
        result = await self.session.execute(stmt)
        return result.scalars().all()
        
    async def get_files_by_status(self, status: str, 
                                 document_type: Optional[str] = None,
                                 limit: int = 100) -> List[claim_files]:
        """Get files by status and optional document type."""
        stmt = select(claim_files).where(claim_files.status == status)
        
        if document_type:
            stmt = stmt.where(claim_files.document_type == document_type)
            
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
        
    async def get_expired_files(self, limit: int = 100) -> List[claim_files]:
        """Get files that have expired."""
        current_time = datetime.utcnow()
        
        stmt = select(claim_files).where(
            and_(
                claim_files.expires_at < current_time,
                claim_files.is_deleted == False
            )
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
        
    async def get_files_summary(self, customer_id: Optional[UUID] = None) -> Dict:
        """Get summary statistics for files."""
        stmt = select(
            func.count(claim_files.id).label('total_files'),
            func.sum(claim_files.file_size).label('total_size'),
            func.avg(claim_files.file_size).label('avg_size')
        ).where(claim_files.is_deleted == False)
        
        if customer_id:
            stmt = stmt.where(claim_files.customer_id == customer_id)
            
        result = await self.session.execute(stmt)
        summary = result.one()
        
        # Get status breakdown
        status_stmt = select(
            claim_files.status,
            func.count(claim_files.id).label('count')
        ).where(claim_files.is_deleted == False)
        
        if customer_id:
            status_stmt = status_stmt.where(claim_files.customer_id == customer_id)
            
        status_stmt = status_stmt.group_by(claim_files.status)
        status_result = await self.session.execute(status_stmt)
        status_breakdown = dict(status_result.all())
        
        return {
            'total_files': summary.total_files or 0,
            'total_size': summary.total_size or 0,
            'avg_size': summary.avg_size or 0,
            'status_breakdown': status_breakdown
        }
        
    async def search_files(self, query: str, customer_id: Optional[UUID] = None,
                          limit: int = 50) -> List[claim_files]:
        """Search files by filename or metadata."""
        stmt = select(claim_files).where(
            and_(
                or_(
                    claim_files.original_filename.ilike(f'%{query}%'),
                    claim_files.document_type.ilike(f'%{query}%')
                ),
                claim_files.is_deleted == False
            )
        ).limit(limit)
        
        if customer_id:
            stmt = stmt.where(claim_files.customer_id == customer_id)
            
        result = await self.session.execute(stmt)
        return result.scalars().all()
```

## Phase 3: Security Implementation (Week 4)

### 3.1 Encryption Service

```python
# app/services/encryption_service.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
import structlog

logger = structlog.get_logger(__name__)

class EncryptionService:
    """Service for file encryption and decryption."""
    
    def __init__(self):
        self.encryption_key = self._get_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key."""
        key_str = os.getenv('FILE_ENCRYPTION_KEY')
        if not key_str:
            raise ValueError("FILE_ENCRYPTION_KEY environment variable not set")
            
        # Convert string key to proper Fernet key format
        key_bytes = key_str.encode('utf-8')
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'stable_salt_for_deterministic_keys',
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
        return key
        
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data."""
        try:
            encrypted_data = self.cipher.encrypt(data)
            logger.debug(f"Encrypted {len(data)} bytes to {len(encrypted_data)} bytes")
            return encrypted_data
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
            
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data."""
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data)
            logger.debug(f"Decrypted {len(encrypted_data)} bytes to {len(decrypted_data)} bytes")
            return decrypted_data
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
            
    def encrypt_file(self, file_path: str, output_path: str) -> str:
        """Encrypt a file."""
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                
            encrypted_data = self.encrypt(file_data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
                
            return output_path
            
        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            raise
            
    def decrypt_file(self, encrypted_file_path: str, output_path: str) -> str:
        """Decrypt a file."""
        try:
            with open(encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()
                
            decrypted_data = self.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
                
            return output_path
            
        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            raise
```

### 3.2 Security Middleware

```python
# app/middleware/security.py
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import hashlib
import structlog
from typing import Optional
import redis
import json

logger = structlog.get_logger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for file operations."""
    
    def __init__(self, app: ASGIApp, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.rate_limit_window = 60  # 1 minute
        self.max_requests_per_window = 10
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with security checks."""
        start_time = time.time()
        
        try:
            # Rate limiting
            if await self._is_rate_limited(request):
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"}
                )
                
            # Content type validation for file uploads
            if request.url.path.endswith("/upload") and request.method == "POST":
                is_valid = await self._validate_upload_request(request)
                if not is_valid:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid upload request"}
                    )
                    
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response = self._add_security_headers(response)
            
            # Log security events
            await self._log_security_event(request, response, time.time() - start_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
            
    async def _is_rate_limited(self, request: Request) -> bool:
        """Check if request is rate limited."""
        client_ip = self._get_client_ip(request)
        key = f"rate_limit:{client_ip}:{int(time.time() / self.rate_limit_window)}"
        
        current_count = self.redis.incr(key)
        if current_count == 1:
            self.redis.expire(key, self.rate_limit_window)
            
        return current_count > self.max_requests_per_window
        
    async def _validate_upload_request(self, request: Request) -> bool:
        """Validate file upload request."""
        content_type = request.headers.get("content-type", "")
        
        # Check for multipart form data
        if not content_type.startswith("multipart/form-data"):
            return False
            
        # Check content length
        content_length = request.headers.get("content-length", "0")
        try:
            length = int(content_length)
            max_size = int(os.getenv('MAX_FILE_SIZE', '52428800'))  # 50MB
            if length > max_size:
                return False
        except ValueError:
            return False
            
        return True
        
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host
        
    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response
        
    async def _log_security_event(self, request: Request, response: Response, 
                                 response_time: float):
        """Log security events for monitoring."""
        event = {
            'timestamp': time.time(),
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'response_time': response_time,
            'client_ip': self._get_client_ip(request),
            'user_agent': request.headers.get('user-agent', '')
        }
        
        # Store in Redis for real-time monitoring
        key = f"security_events:{int(time.time() / 60)}"
        self.redis.lpush(key, json.dumps(event))
        self.redis.expire(key, 3600)  # Keep for 1 hour
```

## Phase 4: Testing and Deployment (Week 5)

### 4.1 Testing Strategy

```python
# app/tests/test_file_service.py
import pytest
import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import Mock, AsyncMock

from app.services.file_service import FileService
from app.models import claim_files, Claim, Customer

@pytest.mark.asyncio
class TestFileService:
    
    @pytest.fixture
    async def file_service(self, db_session: AsyncSession):
        return FileService(db_session)
        
    @pytest.fixture
    async def test_customer(self, db_session: AsyncSession):
        customer = Customer(
            id=uuid4(),
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        db_session.add(customer)
        await db_session.flush()
        return customer
        
    @pytest.fixture
    async def test_claim(self, db_session: AsyncSession, test_customer: Customer):
        claim = Claim(
            id=uuid4(),
            customer_id=test_customer.id,
            flight_number="LH1234",
            airline="Lufthansa",
            departure_date="2024-01-01",
            departure_airport="FRA",
            arrival_airport="JFK",
            incident_type="delay"
        )
        db_session.add(claim)
        await db_session.flush()
        return claim
        
    async def test_upload_file_success(self, file_service: FileService, 
                                     test_claim: Claim, test_customer: Customer):
        """Test successful file upload."""
        file_content = b"Test file content"
        filename = "test.pdf"
        
        result = await file_service.upload_file(
            file_content=file_content,
            filename=filename,
            claim_id=test_claim.id,
            customer_id=test_customer.id,
            document_type="boarding_pass",
            mime_type="application/pdf"
        )
        
        assert result['status'] == 'uploaded'
        assert result['filename'] == filename
        assert 'file_id' in result
        
    async def test_upload_duplicate_file(self, file_service: FileService,
                                       test_claim: Claim, test_customer: Customer):
        """Test duplicate file detection."""
        file_content = b"Test file content"
        filename = "test.pdf"
        
        # Upload first file
        result1 = await file_service.upload_file(
            file_content=file_content,
            filename=filename,
            claim_id=test_claim.id,
            customer_id=test_customer.id,
            document_type="boarding_pass",
            mime_type="application/pdf"
        )
        
        # Upload same file again
        result2 = await file_service.upload_file(
            file_content=file_content,
            filename=filename,
            claim_id=test_claim.id,
            customer_id=test_customer.id,
            document_type="boarding_pass",
            mime_type="application/pdf"
        )
        
        assert result2['status'] == 'duplicate'
        assert result2['existing_file_id'] == result1['file_id']
        
    async def test_download_file(self, file_service: FileService,
                               test_claim: Claim, test_customer: Customer):
        """Test file download."""
        file_content = b"Test file content"
        filename = "test.pdf"
        
        # Upload file
        upload_result = await file_service.upload_file(
            file_content=file_content,
            filename=filename,
            claim_id=test_claim.id,
            customer_id=test_customer.id,
            document_type="boarding_pass",
            mime_type="application/pdf"
        )
        
        # Download file
        downloaded_content = await file_service.download_file(upload_result['file_id'])
        
        assert downloaded_content == file_content
        
    async def test_delete_file(self, file_service: FileService,
                             test_claim: Claim, test_customer: Customer):
        """Test file deletion."""
        file_content = b"Test file content"
        filename = "test.pdf"
        
        # Upload file
        upload_result = await file_service.upload_file(
            file_content=file_content,
            filename=filename,
            claim_id=test_claim.id,
            customer_id=test_customer.id,
            document_type="boarding_pass",
            mime_type="application/pdf"
        )
        
        # Delete file
        delete_result = await file_service.delete_file(upload_result['file_id'], test_customer.id)
        
        assert delete_result is True
        
        # Verify file is marked as deleted
        file_info = await file_service.get_file_info(upload_result['file_id'])
        assert file_info['is_deleted'] is True
```

### 4.2 Deployment Scripts

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

echo "Starting Flight Claim File Management System deployment..."

# Configuration
ENVIRONMENT=${ENVIRONMENT:-production}
DOMAIN=${DOMAIN:-yourdomain.com}
NEXTCLOUD_DOMAIN="nextcloud.${DOMAIN}"
API_DOMAIN="api.${DOMAIN}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check available ports
    if netstat -tuln | grep -q ":80 "; then
        log_warning "Port 80 is already in use"
    fi
    
    if netstat -tuln | grep -q ":443 "; then
        log_warning "Port 443 is already in use"
    fi
    
    log_info "Prerequisites check completed"
}

# Generate SSL certificates
generate_ssl_certificates() {
    log_info "Generating SSL certificates..."
    
    mkdir -p certs
    
    # Generate private key
    openssl genrsa -out certs/private.key 4096
    
    # Generate certificate signing request
    openssl req -new -key certs/private.key -out certs/certificate.csr \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=${DOMAIN}"
    
    # Generate self-signed certificate (for development)
    openssl x509 -req -days 365 -in certs/certificate.csr \
        -signkey certs/private.key -out certs/certificate.crt
    
    log_info "SSL certificates generated"
}

# Initialize database
initialize_database() {
    log_info "Initializing database..."
    
    # Start database container
    docker-compose up -d db
    
    # Wait for database to be ready
    until docker-compose exec db pg_isready -U postgres; do
        log_info "Waiting for database to be ready..."
        sleep 5
    done
    
    # Run database migrations
    docker-compose run --rm api alembic upgrade head
    
    log_info "Database initialized"
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    # Build and start all services
    docker-compose -f docker-compose.yml -f docker-compose.nextcloud.yml up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to become healthy..."
    
    services=("db" "redis" "nextcloud-db" "nextcloud-redis" "nextcloud-app")
    
    for service in "${services[@]}"; do
        until docker-compose ps | grep -q "${service}.*healthy"; do
            log_info "Waiting for ${service} to be healthy..."
            sleep 10
        done
    done
    
    log_info "All services are healthy"
}

# Configure Nextcloud
configure_nextcloud() {
    log_info "Configuring Nextcloud..."
    
    # Wait for Nextcloud to be ready
    until curl -f "https://${NEXTCLOUD_DOMAIN}/status.php" &> /dev/null; do
        log_info "Waiting for Nextcloud to be ready..."
        sleep 10
    done
    
    # Install required apps
    docker-compose exec nextcloud-app php occ app:install files_external
    docker-compose exec nextcloud-app php occ app:install encryption
    docker-compose exec nextcloud-app php occ app:install files_accesscontrol
    
    # Enable apps
    docker-compose exec nextcloud-app php occ app:enable files_external
    docker-compose exec nextcloud-app php occ app:enable encryption
    docker-compose exec nextcloud-app php occ app:enable files_accesscontrol
    
    # Configure encryption
    docker-compose exec nextcloud-app php occ encryption:enable
    docker-compose exec nextcloud-app php occ encryption:encrypt-all
    
    log_info "Nextcloud configuration completed"
}

# Run security checks
run_security_checks() {
    log_info "Running security checks..."
    
    # Check SSL configuration
    if curl -I "https://${NEXTCLOUD_DOMAIN}" | grep -q "HTTP/2 200"; then
        log_info "Nextcloud SSL configuration is working"
    else
        log_error "Nextcloud SSL configuration failed"
        exit 1
    fi
    
    # Check API health
    if curl -f "http://${API_DOMAIN}/health" &> /dev/null; then
        log_info "API health check passed"
    else
        log_error "API health check failed"
        exit 1
    fi
    
    log_info "Security checks completed"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Create monitoring directories
    mkdir -p monitoring/{prometheus,grafana,logs}
    
    # Deploy monitoring stack
    docker-compose -f docker-compose.monitoring.yml up -d
    
    log_info "Monitoring setup completed"
}

# Main deployment function
main() {
    log_info "Starting deployment process..."
    
    check_prerequisites
    generate_ssl_certificates
    initialize_database
    deploy_services
    configure_nextcloud
    run_security_checks
    setup_monitoring
    
    log_info "Deployment completed successfully!"
    log_info "Nextcloud URL: https://${NEXTCLOUD_DOMAIN}"
    log_info "API URL: https://${API_DOMAIN}"
    log_info "Monitoring URL: https://monitoring.${DOMAIN}"
    
    # Show next steps
    echo ""
    log_info "Next steps:"
    echo "1. Update DNS records to point to your server"
    echo "2. Configure backup procedures"
    echo "3. Set up log rotation"
    echo "4. Configure alerting"
    echo "5. Run performance tests"
    echo "6. Schedule security audits"
}

# Run main function
main "$@"
```

## Phase 5: Operations and Maintenance

### 5.1 Backup Procedures

```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="/backup/$(date +%Y%m%d_%H%M%S)"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

# Backup database
docker-compose exec -T db pg_dump -U postgres flight_claim > "$BACKUP_DIR/database.sql"

# Backup Nextcloud data
docker run --rm -v nextcloud_data:/source:ro -v "$BACKUP_DIR":/backup alpine \
    tar czf /backup/nextcloud_data.tar.gz -C /source .

# Backup configuration files
cp -r config "$BACKUP_DIR/"

# Upload to S3 (optional)
if [ -n "$AWS_S3_BUCKET" ]; then
    aws s3 sync "$BACKUP_DIR" "s3://$AWS_S3_BUCKET/backups/$(basename "$BACKUP_DIR")"
fi

# Clean up old backups
find /backup -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
```

### 5.2 Health Monitoring

```python
# scripts/health_check.py
import requests
import sys
import json
from datetime import datetime

def check_service_health(url, service_name):
    """Check if a service is healthy."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✓ {service_name} is healthy")
            return True
        else:
            print(f"✗ {service_name} is unhealthy (status: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ {service_name} is unreachable: {e}")
        return False

def main():
    """Run health checks for all services."""
    services = [
        ("http://localhost:8000/health", "API Service"),
        ("https://nextcloud.localhost/status.php", "Nextcloud"),
        ("http://localhost:8080/health", "File Processor"),
        ("http://localhost:9090/-/healthy", "Prometheus"),
        ("http://localhost:3000/api/health", "Grafana"),
    ]
    
    healthy_count = 0
    total_count = len(services)
    
    print(f"Health Check Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    for url, name in services:
        if check_service_health(url, name):
            healthy_count += 1
    
    print("=" * 50)
    print(f"Overall Health: {healthy_count}/{total_count} services healthy")
    
    if healthy_count == total_count:
        print("✓ All services are operational")
        sys.exit(0)
    else:
        print("✗ Some services are experiencing issues")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 5.3 Log Analysis

```python
# scripts/log_analyzer.py
import re
import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import argparse

class LogAnalyzer:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.errors = []
        self.warnings = []
        self.access_patterns = defaultdict(int)
        self.ip_addresses = Counter()
        self.status_codes = Counter()
        
    def analyze(self):
        """Analyze log file and extract insights."""
        with open(self.log_file_path, 'r') as f:
            for line in f:
                self._process_log_line(line)
                
        self._generate_report()
        
    def _process_log_line(self, line):
        """Process a single log line."""
        # Extract IP address
        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
        if ip_match:
            self.ip_addresses[ip_match.group(1)] += 1
            
        # Extract status code
        status_match = re.search(r'HTTP/\d\.\d" (\d{3})', line)
        if status_match:
            self.status_codes[status_match.group(1)] += 1
            
        # Extract errors and warnings
        if 'ERROR' in line:
            self.errors.append(line.strip())
        elif 'WARNING' in line:
            self.warnings.append(line.strip())
            
    def _generate_report(self):
        """Generate analysis report."""
        print("Log Analysis Report")
        print("=" * 50)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Log File: {self.log_file_path}")
        print()
        
        print("Summary Statistics:")
        print(f"- Total Errors: {len(self.errors)}")
        print(f"- Total Warnings: {len(self.warnings)}")
        print(f"- Unique IP Addresses: {len(self.ip_addresses)}")
        print()
        
        print("Top IP Addresses:")
        for ip, count in self.ip_addresses.most_common(10):
            print(f"  {ip}: {count} requests")
        print()
        
        print("Status Code Distribution:")
        for status, count in self.status_codes.most_common():
            print(f"  {status}: {count} responses")
        print()
        
        if self.errors:
            print("Recent Errors:")
            for error in self.errors[-5:]:
                print(f"  {error}")
            print()
            
        if self.warnings:
            print("Recent Warnings:")
            for warning in self.warnings[-5:]:
                print(f"  {warning}")
            print()
            
        # Security analysis
        self._security_analysis()
        
    def _security_analysis(self):
        """Perform security-focused analysis."""
        print("Security Analysis:")
        
        # Check for suspicious patterns
        suspicious_ips = []
        for ip, count in self.ip_addresses.items():
            if count > 100:  # High request count
                suspicious_ips.append(ip)
                
        if suspicious_ips:
            print(f"⚠️  Suspicious IP addresses detected: {', '.join(suspicious_ips)}")
            
        # Check for error patterns
        error_4xx = sum(count for status, count in self.status_codes.items() if status.startswith('4'))
        error_5xx = sum(count for status, count in self.status_codes.items() if status.startswith('5'))
        
        if error_4xx > 50:
            print(f"⚠️  High number of client errors: {error_4xx}")
        if error_5xx > 10:
            print(f"⚠️  High number of server errors: {error_5xx}")
            
        print()

def main():
    parser = argparse.ArgumentParser(description='Analyze log files')
    parser.add_argument('log_file', help='Path to log file')
    parser.add_argument('--output', help='Output file for JSON results')
    
    args = parser.parse_args()
    
    analyzer = LogAnalyzer(args.log_file)
    analyzer.analyze()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                'errors': analyzer.errors,
                'warnings': analyzer.warnings,
                'ip_addresses': dict(analyzer.ip_addresses),
                'status_codes': dict(analyzer.status_codes)
            }, f, indent=2)
        print(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Nextcloud Connection Issues
```bash
# Check Nextcloud logs
docker-compose logs nextcloud-app

# Check database connection
docker-compose exec nextcloud-app php occ db:add-missing-indices

# Reset Nextcloud admin password
docker-compose exec nextcloud-app php occ user:resetpassword admin
```

#### 2. File Upload Failures
```bash
# Check file processor logs
docker-compose logs file-processor

# Check available disk space
df -h

# Check file permissions
docker-compose exec nextcloud-app ls -la /var/www/html/data
```

#### 3. Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose logs db

# Test database connection
docker-compose exec db pg_isready -U postgres

# Check database migrations
docker-compose run --rm api alembic current
```

#### 4. Performance Issues
```bash
# Check system resources
htop

# Check Docker container stats
docker stats

# Check Redis performance
docker-compose exec redis redis-cli info stats
```

#### 5. SSL Certificate Issues
```bash
# Check certificate expiration
openssl x509 -in certs/certificate.crt -text -noout | grep "Not After"

# Renew certificates
docker-compose exec traefik acme.sh --renew -d yourdomain.com

# Check Traefik logs
docker-compose logs traefik
```

## Security Checklist

### Pre-deployment Security Review
- [ ] All secrets are properly encrypted and stored
- [ ] Database connections use SSL/TLS
- [ ] File encryption is enabled and tested
- [ ] Access control policies are implemented
- [ ] Audit logging is configured
- [ ] Rate limiting is enabled
- [ ] Input validation is comprehensive
- [ ] Error messages don't leak sensitive information
- [ ] Security headers are configured
- [ ] Vulnerability scanning is performed

### Ongoing Security Maintenance
- [ ] Regular security updates
- [ ] Log monitoring and analysis
- [ ] Access review and cleanup
- [ ] Backup encryption and testing
- [ ] Incident response procedures
- [ ] Security awareness training
- [ ] Compliance audits
- [ ] Penetration testing
- [ ] Security metrics review
- [ ] Threat assessment updates

This implementation guide provides a comprehensive roadmap for deploying and maintaining the file management system. Follow the phases sequentially and adapt the configuration to your specific environment and requirements.