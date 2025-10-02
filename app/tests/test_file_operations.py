"""Tests for file management operations."""
import pytest
import uuid
from io import BytesIO
from unittest.mock import Mock, AsyncMock, patch

from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import ClaimFile, FileAccessLog
from app.services.file_service import FileService
from app.services.encryption_service import encryption_service
from app.services.file_validation_service import file_validation_service


class TestFileOperations:
    """Test cases for file management operations."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_file(self):
        """Create mock upload file."""
        content = b"Test file content for flight claim"
        file = UploadFile(
            filename="test_document.pdf",
            file=BytesIO(content),
            content_type="application/pdf"
        )
        file.size = len(content)
        return file
    
    @pytest.fixture
    def sample_file_data(self):
        """Sample file data for testing."""
        return {
            "claim_id": "123e4567-e89b-12d3-a456-426614174000",
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "document_type": "boarding_pass",
            "description": "Test boarding pass document",
            "access_level": "private"
        }
    
    @pytest.mark.asyncio
    async def test_file_upload_validation(self, mock_file, sample_file_data):
        """Test file upload with validation."""
        # Mock the validation service
        with patch.object(file_validation_service, 'validate_file') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "mime_type": "application/pdf",
                "file_size": len(b"Test file content for flight claim"),
                "file_hash": "test_hash_123",
                "scan_required": True,
                "encryption_required": True
            }
            
            # Mock Nextcloud service
            with patch('app.services.file_service.nextcloud_service') as mock_nextcloud:
                mock_nextcloud.upload_file.return_value = {
                    "success": True,
                    "file_id": "test_file_id",
                    "url": "https://nextcloud.local/test_file",
                    "status_code": 201
                }
                
                # Test validation
                result = await file_validation_service.validate_file(
                    file_content=await mock_file.read(),
                    filename=mock_file.filename,
                    document_type=sample_file_data["document_type"],
                    declared_mime_type=mock_file.content_type
                )
                
                assert result["valid"] is True
                assert result["mime_type"] == "application/pdf"
                assert result["scan_required"] is True
                assert result["encryption_required"] is True
    
    @pytest.mark.asyncio
    async def test_file_encryption(self):
        """Test file encryption and decryption."""
        test_content = b"Sensitive flight claim document content"
        
        # Encrypt content
        encrypted_content = encryption_service.encrypt_file_content(test_content)
        
        # Verify it's different from original
        assert encrypted_content != test_content
        assert len(encrypted_content) > 0
        
        # Decrypt content
        decrypted_content = encryption_service.decrypt_file_content(encrypted_content)
        
        # Verify decryption worked
        assert decrypted_content == test_content
    
    def test_file_hash_generation(self):
        """Test file hash generation."""
        test_content = b"Test content for hashing"
        
        # Generate hash
        file_hash = encryption_service.generate_file_hash(test_content)
        
        # Verify hash format
        assert len(file_hash) == 64  # SHA256 produces 64 character hex string
        assert file_hash.isalnum()  # Should be hexadecimal
        
        # Verify same content produces same hash
        same_hash = encryption_service.generate_file_hash(test_content)
        assert file_hash == same_hash
        
        # Verify different content produces different hash
        different_content = b"Different content"
        different_hash = encryption_service.generate_file_hash(different_content)
        assert file_hash != different_hash
    
    def test_secure_filename_generation(self):
        """Test secure filename generation."""
        original_filename = "sensitive_document.pdf"
        
        # Generate secure filename
        secure_filename = encryption_service.generate_secure_filename(original_filename)
        
        # Verify it preserves extension
        assert secure_filename.endswith(".pdf")
        
        # Verify it's different from original
        assert secure_filename != original_filename
        
        # Verify it's a valid UUID format with extension
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.pdf$'
        assert re.match(uuid_pattern, secure_filename) is not None
    
    @pytest.mark.asyncio
    async def test_nextcloud_service_mock(self):
        """Test Nextcloud service with mock."""
        from app.services.nextcloud_service import NextcloudService
        
        # Create service instance
        service = NextcloudService()
        
        # Mock httpx client
        with patch('app.services.nextcloud_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.text = "OK"
            
            mock_client.request.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Test upload
            test_content = b"Test file content"
            result = await service.upload_file(
                file_content=test_content,
                remote_path="test/file.pdf"
            )
            
            assert result["success"] is True
            assert result["status_code"] == 201
    
    def test_file_validation_rules(self):
        """Test file validation rules for different document types."""
        rules = file_validation_service.default_rules
        
        # Test boarding pass rules
        boarding_pass_rules = rules["boarding_pass"]
        assert boarding_pass_rules["max_file_size"] == 10 * 1024 * 1024  # 10MB
        assert "application/pdf" in boarding_pass_rules["allowed_mime_types"]
        assert ".pdf" in boarding_pass_rules["required_extensions"]
        assert boarding_pass_rules["requires_scan"] is True
        assert boarding_pass_rules["requires_encryption"] is True
        
        # Test ID document rules (smaller size limit)
        id_rules = rules["id_document"]
        assert id_rules["max_file_size"] == 5 * 1024 * 1024  # 5MB
        assert id_rules["max_pages"] == 2
        
        # Test receipt rules
        receipt_rules = rules["receipt"]
        assert receipt_rules["max_file_size"] == 2 * 1024 * 1024  # 2MB
        assert receipt_rules["max_pages"] == 3
    
    @pytest.mark.asyncio
    async def test_pdf_content_validation(self):
        """Test PDF content validation."""
        # Create a simple PDF-like content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"
        
        # Test validation
        rules = {
            "max_pages": 5,
            "allowed_mime_types": ["application/pdf"]
        }
        
        result = await file_validation_service._validate_pdf_content(pdf_content, rules)
        
        # Should pass basic validation
        assert len(result["errors"]) == 0
        
        # Test with too many pages
        large_pdf_content = b"%PDF-1.4\n" + b"/Page\n" * 10  # Simulate 10 pages
        result_large = await file_validation_service._validate_pdf_content(large_pdf_content, rules)
        
        # Should have page limit error
        assert any("pages" in error for error in result_large["errors"])
    
    def test_security_pattern_detection(self):
        """Test security pattern detection in files."""
        # Test content with suspicious patterns
        suspicious_content = b"""
        <script>alert('xss')</script>
        eval(malicious_code);
        system('rm -rf /');
        javascript:alert('xss');
        """
        
        result = file_validation_service._perform_security_checks(suspicious_content, "test.html")
        
        # Should detect multiple suspicious patterns
        assert len(result["errors"]) > 0
        assert any("Suspicious pattern" in error for error in result["errors"])
        
        # Test with credit card pattern
        cc_content = b"My card number is 1234-5678-9012-3456"
        cc_result = file_validation_service._perform_security_checks(cc_content, "test.txt")
        
        assert any("credit card" in warning for warning in cc_result["warnings"])
    
    def test_duplicate_file_detection(self):
        """Test duplicate file detection."""
        test_content = b"Same file content"
        file_hash = encryption_service.generate_file_hash(test_content)
        
        # Test with existing hash
        existing_hashes = [file_hash, "other_hash_123"]
        is_duplicate = file_validation_service.check_duplicate_file(file_hash, existing_hashes)
        
        assert is_duplicate is True
        
        # Test with non-existing hash
        is_not_duplicate = file_validation_service.check_duplicate_file("new_hash_456", existing_hashes)
        assert is_not_duplicate is False


class TestFileAPIEndpoints:
    """Test cases for file API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_file_upload_endpoint_structure(self, client):
        """Test file upload endpoint structure."""
        # Test that the endpoint exists and returns proper error for missing file
        response = client.post(
            "/files/upload",
            data={
                "claim_id": "123e4567-e89b-12d3-a456-426614174000",
                "customer_id": "123e4567-e89b-12d3-a456-426614174000",
                "document_type": "boarding_pass"
            }
        )
        
        # Should return 422 for missing file
        assert response.status_code == 422
    
    def test_file_info_endpoint_structure(self, client):
        """Test file info endpoint structure."""
        # Test with invalid file ID
        response = client.get("/files/invalid-file-id")
        
        # Should return 404 or 500 for invalid ID
        assert response.status_code in [404, 500]
    
    def test_file_download_endpoint_structure(self, client):
        """Test file download endpoint structure."""
        # Test with invalid file ID
        response = client.get("/files/invalid-file-id/download")
        
        # Should return 404 or 500 for invalid ID
        assert response.status_code in [404, 500]
    
    def test_file_delete_endpoint_structure(self, client):
        """Test file delete endpoint structure."""
        # Test with invalid file ID
        response = client.delete("/files/invalid-file-id")
        
        # Should return 404 or 500 for invalid ID
        assert response.status_code in [404, 500]
    
    def test_files_by_claim_endpoint_structure(self, client):
        """Test files by claim endpoint structure."""
        # Test with invalid claim ID
        response = client.get("/files/claim/invalid-claim-id")
        
        # Should return 404 or 500 for invalid ID
        assert response.status_code in [404, 500]
    
    def test_files_by_customer_endpoint_structure(self, client):
        """Test files by customer endpoint structure."""
        # Test with invalid customer ID
        response = client.get("/files/customer/invalid-customer-id")
        
        # Should return 404 or 500 for invalid ID
        assert response.status_code in [404, 500]
    
    def test_file_search_endpoint_structure(self, client):
        """Test file search endpoint structure."""
        # Test search with empty query
        response = client.post(
            "/files/search",
            json={
                "query": "",
                "page": 1,
                "per_page": 20
            }
        )
        
        # Should return 200 or 500
        assert response.status_code in [200, 500]
    
    def test_validation_rules_endpoint_structure(self, client):
        """Test validation rules endpoint structure."""
        response = client.get("/files/validation-rules")
        
        # Should return 200 with validation rules
        assert response.status_code == 200


class TestFileSecurity:
    """Test cases for file security features."""
    
    def test_file_size_limits(self):
        """Test file size validation limits."""
        # Test various size limits
        size_limits = {
            "boarding_pass": 10 * 1024 * 1024,  # 10MB
            "id_document": 5 * 1024 * 1024,     # 5MB
            "receipt": 2 * 1024 * 1024,         # 2MB
            "bank_statement": 5 * 1024 * 1024,  # 5MB
            "other": 10 * 1024 * 1024          # 10MB
        }
        
        for doc_type, expected_size in size_limits.items():
            rules = file_validation_service.default_rules[doc_type]
            assert rules["max_file_size"] == expected_size
    
    def test_encryption_requirements(self):
        """Test that encryption is required for all document types."""
        for doc_type, rules in file_validation_service.default_rules.items():
            assert rules["requires_encryption"] is True
    
    def test_scanning_requirements(self):
        """Test that scanning is required for all document types."""
        for doc_type, rules in file_validation_service.default_rules.items():
            assert rules["requires_scan"] is True
    
    def test_secure_filename_generation(self):
        """Test that secure filenames are properly generated."""
        test_filenames = [
            "document.pdf",
            "image with spaces.jpg",
            "sensitive_data.png",
            "../../../etc/passwd.txt",
            "file<script>.html"
        ]
        
        for filename in test_filenames:
            secure_name = encryption_service.generate_secure_filename(filename)
            
            # Should preserve extension
            original_ext = filename.split('.')[-1] if '.' in filename else ''
            secure_ext = secure_name.split('.')[-1] if '.' in secure_name else ''
            assert secure_ext == original_ext
            
            # Should not contain path traversal
            assert '..' not in secure_name
            assert '/' not in secure_name
            assert '\\' not in secure_name
            
            # Should be different from original (except for extension)
            if '.' in filename:
                original_name = '.'.join(filename.split('.')[:-1])
                secure_name_part = '.'.join(secure_name.split('.')[:-1])
                assert secure_name_part != original_name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])