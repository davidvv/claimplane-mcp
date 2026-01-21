"""File validation service for security and compliance."""
import json
import mimetypes
import os
import re
from typing import Dict, Any, Optional, List

from fastapi import HTTPException, status


class FileValidationService:
    """Service for validating uploaded files."""
    
    def __init__(self):
        """Initialize file validation service."""
        from app.config import config
        self.max_file_size = config.MAX_FILE_SIZE
        
        # Default validation rules for different document types
        self.default_rules = {
            "boarding_pass": {
                "max_file_size": 10 * 1024 * 1024,  # 10MB
                "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png", "image/webp", "message/rfc822", "application/octet-stream"],
                "required_extensions": [".pdf", ".jpg", ".jpeg", ".png", ".webp", ".eml"],
                "max_pages": 15,
                "requires_scan": True,
                "requires_encryption": True
            },
            "id_document": {
                "max_file_size": 5 * 1024 * 1024,  # 5MB
                "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png", "image/webp"],
                "required_extensions": [".pdf", ".jpg", ".jpeg", ".png", ".webp"],
                "max_pages": 2,
                "requires_scan": True,
                "requires_encryption": True
            },
            "receipt": {
                "max_file_size": 2 * 1024 * 1024,  # 2MB
                "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png", "image/webp"],
                "required_extensions": [".pdf", ".jpg", ".jpeg", ".png", ".webp"],
                "max_pages": 3,
                "requires_scan": True,
                "requires_encryption": True
            },
            "bank_statement": {
                "max_file_size": 5 * 1024 * 1024,  # 5MB
                "allowed_mime_types": ["application/pdf"],
                "required_extensions": [".pdf"],
                "max_pages": 10,
                "requires_scan": True,
                "requires_encryption": True
            },
            "flight_ticket": {
                "max_file_size": 5 * 1024 * 1024,  # 5MB
                "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png", "image/webp", "message/rfc822", "application/octet-stream"],
                "required_extensions": [".pdf", ".jpg", ".jpeg", ".png", ".webp", ".eml"],
                "max_pages": 15,
                "requires_scan": True,
                "requires_encryption": True
            },
            "delay_certificate": {
                "max_file_size": 2 * 1024 * 1024,  # 2MB
                "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png", "image/webp"],
                "required_extensions": [".pdf", ".jpg", ".jpeg", ".png", ".webp"],
                "max_pages": 2,
                "requires_scan": True,
                "requires_encryption": True
            },
            "cancellation_notice": {
                "max_file_size": 2 * 1024 * 1024,  # 2MB
                "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png", "image/webp"],
                "required_extensions": [".pdf", ".jpg", ".jpeg", ".png", ".webp"],
                "max_pages": 2,
                "requires_scan": True,
                "requires_encryption": True
            },
            "other": {
                "max_file_size": 10 * 1024 * 1024,  # 10MB
                "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png", "image/webp", "text/plain"],
                "required_extensions": [".pdf", ".jpg", ".jpeg", ".png", ".webp", ".txt"],
                "max_pages": 20,
                "requires_scan": True,
                "requires_encryption": True
            }
        }
    
    async def validate_file(self, file_content: bytes, filename: str, document_type: str, 
                          declared_mime_type: str, file_size: Optional[int] = None) -> Dict[str, Any]:
        """Comprehensive file validation."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "mime_type": None,
            "file_size": len(file_content) if file_size is None else file_size,
            "file_hash": None,
            "scan_required": False,
            "encryption_required": False
        }
        
        try:
            # Get validation rules for document type
            rules = self.default_rules.get(document_type)
            if not rules:
                validation_result["errors"].append(f"Unknown document type: {document_type}")
                validation_result["valid"] = False
                return validation_result
            
            # File size validation
            if validation_result["file_size"] > rules["max_file_size"]:
                validation_result["errors"].append(
                    f"File size {validation_result['file_size']} exceeds maximum {rules['max_file_size']}"
                )
                validation_result["valid"] = False
            
            # MIME type validation
            detected_mime_type = self._detect_mime_type(file_content, filename)
            validation_result["mime_type"] = detected_mime_type
            
            if detected_mime_type not in rules["allowed_mime_types"]:
                validation_result["errors"].append(
                    f"MIME type {detected_mime_type} not allowed for {document_type}"
                )
                validation_result["valid"] = False
            
            # File extension validation
            if not self._validate_file_extension(filename, rules["required_extensions"]):
                validation_result["errors"].append(
                    f"File extension not allowed for {document_type}"
                )
                validation_result["valid"] = False
            
            # Content validation for PDFs
            if detected_mime_type == "application/pdf":
                pdf_validation = await self._validate_pdf_content(file_content, rules)
                validation_result["errors"].extend(pdf_validation["errors"])
                validation_result["warnings"].extend(pdf_validation["warnings"])
                if pdf_validation["errors"]:
                    validation_result["valid"] = False
            
            # Security checks
            security_result = await self._perform_security_checks(file_content, filename)
            validation_result["errors"].extend(security_result["errors"])
            validation_result["warnings"].extend(security_result["warnings"])
            if security_result["errors"]:
                validation_result["valid"] = False
            
            # Generate file hash
            import hashlib
            validation_result["file_hash"] = hashlib.sha256(file_content).hexdigest()
            
            # Set security requirements
            validation_result["scan_required"] = rules.get("requires_scan", False)
            validation_result["encryption_required"] = rules.get("requires_encryption", False)
            
            return validation_result
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["valid"] = False
            return validation_result
    
    def _detect_mime_type(self, file_content: bytes, filename: str) -> str:
        """Detect MIME type from file content and filename."""
        try:
            import magic
            
            # Try to detect from content first
            try:
                mime_type = magic.from_buffer(file_content, mime=True)
                if mime_type and mime_type != "application/octet-stream":
                    return mime_type
            except Exception as e:
                # Log the error but continue with fallback
                print(f"Magic library detection failed: {str(e)}")
                pass
            
        except ImportError as e:
            # Handle case where libmagic is not available
            print(f"libmagic not available: {str(e)}")
        
        # Fallback to filename-based detection
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"
    
    def _validate_file_extension(self, filename: str, allowed_extensions: List[str]) -> bool:
        """Validate file extension."""
        import os
        _, ext = os.path.splitext(filename.lower())
        return ext in allowed_extensions
    
    async def _validate_pdf_content(self, file_content: bytes, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PDF content."""
        result = {"errors": [], "warnings": []}
        
        try:
            # Basic PDF validation - check for PDF header
            if not file_content.startswith(b"%PDF"):
                result["errors"].append("File does not appear to be a valid PDF")
                return result
            
            # Check for PDF version
            pdf_version = file_content[1:8].decode('utf-8', errors='ignore')
            if not pdf_version.startswith("PDF-"):
                result["warnings"].append("Unusual PDF version format")
            
            # Check for suspicious content patterns
            content_str = file_content.decode('utf-8', errors='ignore')
            
            # Look for JavaScript (potential security risk)
            if "JavaScript" in content_str or "/JS" in content_str:
                result["warnings"].append("PDF contains JavaScript - potential security risk")
            
            # Look for embedded files
            if "/EmbeddedFile" in content_str:
                result["warnings"].append("PDF contains embedded files")
            
            # Check file size against page limit (rough estimate)
            estimated_pages = len([m for m in re.finditer(b"/Page", file_content)])
            max_pages = rules.get("max_pages", 10)
            if estimated_pages > max_pages:
                result["errors"].append(f"PDF appears to have {estimated_pages} pages, maximum allowed is {max_pages}")
            
        except Exception as e:
            result["errors"].append(f"PDF validation error: {str(e)}")
        
        return result
    
    async def _perform_security_checks(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Perform security checks on file content."""
        result = {"errors": [], "warnings": []}
        
        try:
            # Check for suspicious patterns
            content_str = file_content.decode('utf-8', errors='ignore')
            
            # Check for potential malware signatures (basic patterns)
            suspicious_patterns = [
                r'eval\s*\(',
                r'exec\s*\(',
                r'system\s*\(',
                r'passthru\s*\(',
                r'shell_exec\s*\(',
                r'<script[^>]*>',
                r'javascript:',
                r'onload\s*=',
                r'onerror\s*='
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, content_str, re.IGNORECASE):
                    result["errors"].append(f"Suspicious pattern detected: {pattern}")
            
            # Check for credit card numbers (basic pattern)
            credit_card_pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
            if re.search(credit_card_pattern, content_str):
                result["warnings"].append("Potential credit card number detected")
            
            # Check for SSN patterns (basic)
            ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
            if re.search(ssn_pattern, content_str):
                result["warnings"].append("Potential SSN detected")
            
            # Check for excessive size (indicating potential zip bomb or similar)
            if len(file_content) > 50 * 1024 * 1024:  # 50MB
                result["errors"].append("File size exceeds security limits")
            
            # Check for compression bombs (very high compression ratio)
            if len(file_content) < 1000 and b"FlateDecode" in file_content:
                result["warnings"].append("Potential compression bomb detected")
            
        except Exception as e:
            result["errors"].append(f"Security check error: {str(e)}")
        
        return result
    
    def check_duplicate_file(self, file_hash: str, existing_hashes: List[str]) -> bool:
        """Check if file is a duplicate based on hash."""
        return file_hash in existing_hashes


# Global file validation service instance
file_validation_service = FileValidationService()