"""Encryption service for file security."""
import base64
import hashlib
import os
from typing import Optional, Dict, Any

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
    
    def verify_integrity(self, encrypted_data: bytes, expected_hash: str, original_data: Optional[bytes] = None) -> bool:
        """Verify file integrity by comparing hashes."""
        try:
            if original_data is not None:
                actual_hash = self.generate_file_hash(original_data)
            else:
                # Note: This only works for non-streamed/single-token files.
                # For streamed files, we must rely on the hash calculated during upload/download.
                decrypted_data = self.decrypt_data(encrypted_data)
                actual_hash = self.generate_file_hash(decrypted_data)

            return actual_hash == expected_hash
        except Exception:
            return False

    def get_encrypted_chunk_size(self, chunk_size: int) -> int:
        """Calculate the size of a Fernet token for a given plaintext chunk size."""
        # AES-128-CBC PKCS7 padding
        pad_len = 16 - (chunk_size % 16)
        padded_size = chunk_size + pad_len
        
        # Fernet Overhead: Version(1) + Timestamp(8) + IV(16) + HMAC(32) = 57 bytes
        binary_size = 57 + padded_size
        
        # Base64 expansion
        return 4 * ((binary_size + 2) // 3)

    def calculate_total_encrypted_size(self, total_size: int, chunk_size: int) -> int:
        """Calculate the total size of the encrypted file composed of concatenated Fernet tokens."""
        if total_size == 0:
            return self.get_encrypted_chunk_size(0)
            
        num_full_chunks = total_size // chunk_size
        last_chunk_size = total_size % chunk_size
        
        full_chunk_encrypted_size = self.get_encrypted_chunk_size(chunk_size)
        total = num_full_chunks * full_chunk_encrypted_size
        
        if last_chunk_size > 0:
            total += self.get_encrypted_chunk_size(last_chunk_size)
            
        return total


# Global encryption service instance
encryption_service = EncryptionService()