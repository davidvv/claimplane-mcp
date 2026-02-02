
import os
import io
# import pytest
from app.services.encryption_service import EncryptionService
from app.config import config

def test_large_file_encryption_decryption():
    service = EncryptionService()
    # 60MB file to exceed Fernet "problematic" threshold mentioned by user
    large_data = os.urandom(60 * 1024 * 1024) 
    
    # Current implementation uses chunked Fernet in file_service.py
    # But EncryptionService itself only has encrypt_data/decrypt_data for the whole thing.
    # The user says corruption happens for large files.
    
    print("Encrypting large data...")
    # This might fail with memory error if Fernet is used on 60MB at once
    try:
        encrypted = service.encrypt_data(large_data)
        print(f"Encrypted size: {len(encrypted)}")
        
        print("Decrypting large data...")
        decrypted = service.decrypt_data(encrypted)
        
        assert decrypted == large_data
        print("Success!")
    except Exception as e:
        print(f"Failed: {e}")
        raise

if __name__ == "__main__":
    test_large_file_encryption_decryption()
