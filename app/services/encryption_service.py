"""Encryption service for file security."""
import base64
import hashlib
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import config


class EncryptionService:
    """Service for encrypting and decrypting files."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize encryption service with key."""
        self.encryption_key = encryption_key or config.FILE_ENCRYPTION_KEY
        
        # Validate the encryption key
        if not self.encryption_key:
            raise ValueError("FILE_ENCRYPTION_KEY is required and cannot be empty")
        
        # Ensure it's a valid Fernet key
        try:
            self.cipher_suite = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key format: {e}")
    
    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using Fernet encryption."""
        return self.cipher_suite.encrypt(data)
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using Fernet encryption."""
        return self.cipher_suite.decrypt(encrypted_data)
    
    def encrypt_file_content(self, file_content: bytes) -> bytes:
        """Encrypt file content."""
        return self.encrypt_data(file_content)
    
    def decrypt_file_content(self, encrypted_content: bytes) -> bytes:
        """Decrypt file content."""
        return self.decrypt_data(encrypted_content)
    
    def generate_file_hash(self, file_content: bytes) -> str:
        """Generate SHA256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()
    
    def generate_secure_filename(self, original_filename: str) -> str:
        """Generate a secure filename using hash."""
        # Extract file extension
        import uuid
        import os
        
        _, ext = os.path.splitext(original_filename)
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{ext.lower()}"
    
    def verify_integrity(self, encrypted_data: bytes, expected_hash: str) -> bool:
        """Verify file integrity by comparing hashes."""
        try:
            decrypted_data = self.decrypt_data(encrypted_data)
            actual_hash = self.generate_file_hash(decrypted_data)
            return actual_hash == expected_hash
        except Exception:
            return False


# Global encryption service instance
encryption_service = EncryptionService()