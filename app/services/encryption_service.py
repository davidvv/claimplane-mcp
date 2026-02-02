"""Encryption service for file security."""
import base64
import hashlib
import os
import struct
from typing import Optional, Dict, Any, Generator

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import config


class EncryptionService:
    """Service for encrypting and decrypting files using AES-256-GCM streaming."""
    
    # Format constants
    GCM_MAGIC = b"EACGCM"
    GCM_VERSION = 2  # V2 includes chunk length
    HEADER_STRUCT = ">6sB I 8s"  # magic(6), version(1), default_chunk_size(I), master_nonce(8)
    HEADER_SIZE = struct.calcsize(HEADER_STRUCT)
    
    CHUNK_HEADER_STRUCT = ">I I 16s" # ciphertext_len(I), nonce_counter(I), tag(16)
    CHUNK_HEADER_SIZE = struct.calcsize(CHUNK_HEADER_STRUCT)

    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize encryption service with key."""
        self.encryption_key_str = encryption_key or config.FILE_ENCRYPTION_KEY
        
        # Validate the encryption key
        if not self.encryption_key_str:
            raise ValueError("FILE_ENCRYPTION_KEY is required and cannot be empty")
        
        # For backward compatibility with Fernet
        try:
            self.fernet_key = self.encryption_key_str.encode() if isinstance(self.encryption_key_str, str) else self.encryption_key_str
            self.cipher_suite = Fernet(self.fernet_key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key format for Fernet: {e}")
            
        # For AES-GCM (derive 32-byte key from Fernet key which is already 32 bytes after base64 decode)
        try:
            # Fernet keys are 32 bytes base64 encoded. 
            self.raw_key = base64.urlsafe_b64decode(self.fernet_key)
            if len(self.raw_key) != 32:
                # If it's not 32 bytes, hash it to get 32 bytes
                self.raw_key = hashlib.sha256(self.raw_key).digest()
            self.aes_gcm = AESGCM(self.raw_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize AES-GCM: {e}")

    def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt data. Now uses AES-GCM by default but wrapped in a single chunk 
        for small data compatibility.
        """
        master_nonce = os.urandom(8)
        chunk_size = len(data)
        
        header = struct.pack(self.HEADER_STRUCT, self.GCM_MAGIC, self.GCM_VERSION, chunk_size, master_nonce)
        
        # Chunk 0
        nonce = master_nonce + struct.pack(">I", 0)
        ciphertext_with_tag = self.aes_gcm.encrypt(nonce, data, None)
        tag = ciphertext_with_tag[-16:]
        ciphertext = ciphertext_with_tag[:-16]
        
        chunk_header = struct.pack(self.CHUNK_HEADER_STRUCT, len(ciphertext), 0, tag)
        
        return header + chunk_header + ciphertext

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data, supporting both Fernet and AES-GCM."""
        if encrypted_data.startswith(self.GCM_MAGIC):
            # AES-GCM
            try:
                header = encrypted_data[:self.HEADER_SIZE]
                magic, version, def_chunk_size, master_nonce = struct.unpack(self.HEADER_STRUCT, header)
                
                if version != 2:
                    raise ValueError(f"Unsupported GCM version: {version}")
                
                result = b""
                offset = self.HEADER_SIZE
                while offset < len(encrypted_data):
                    chunk_header_data = encrypted_data[offset:offset+self.CHUNK_HEADER_SIZE]
                    if len(chunk_header_data) < self.CHUNK_HEADER_SIZE:
                        break
                        
                    c_len, nonce_counter, tag = struct.unpack(self.CHUNK_HEADER_STRUCT, chunk_header_data)
                    offset += self.CHUNK_HEADER_SIZE
                    
                    ciphertext = encrypted_data[offset : offset + c_len]
                    offset += c_len
                    
                    nonce = master_nonce + struct.pack(">I", nonce_counter)
                    result += self.aes_gcm.decrypt(nonce, ciphertext + tag, None)
                
                return result
            except Exception as e:
                raise ValueError(f"AES-GCM decryption failed: {e}")
        else:
            # Fallback to Fernet
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
        import uuid
        _, ext = os.path.splitext(original_filename)
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{ext.lower()}"

    def verify_integrity(self, encrypted_data: bytes, expected_hash: str, original_data: Optional[bytes] = None) -> bool:
        """Verify file integrity by comparing hashes."""
        try:
            if original_data is not None:
                actual_hash = self.generate_file_hash(original_data)
            else:
                decrypted_data = self.decrypt_data(encrypted_data)
                actual_hash = self.generate_file_hash(decrypted_data)

            return actual_hash == expected_hash
        except Exception:
            return False

    # Streaming methods
    
    def get_gcm_overhead(self) -> int:
        """Return the overhead per chunk for GCM."""
        return self.CHUNK_HEADER_SIZE

    def calculate_total_encrypted_size(self, total_size: int, chunk_size: int) -> int:
        """Calculate the total size of the encrypted file."""
        if total_size == 0:
            return self.HEADER_SIZE + self.CHUNK_HEADER_SIZE
            
        num_chunks = (total_size + chunk_size - 1) // chunk_size
        return self.HEADER_SIZE + (num_chunks * self.CHUNK_HEADER_SIZE) + total_size

    def create_streaming_context(self, chunk_size: int = None) -> Dict[str, Any]:
        """Create a context for streaming encryption."""
        return {
            "initialized": True,
            "master_nonce": os.urandom(8),
            "nonce_counter": 0,
            "chunk_size": chunk_size or config.CHUNK_SIZE,
            "header_sent": False
        }

    def encrypt_chunk(self, chunk: bytes, context: Dict[str, Any]) -> bytes:
        """Encrypt a single chunk using the provided context."""
        result = b""
        if not context.get("header_sent"):
            header = struct.pack(
                self.HEADER_STRUCT, 
                self.GCM_MAGIC, 
                self.GCM_VERSION, 
                context["chunk_size"], 
                context["master_nonce"]
            )
            result += header
            context["header_sent"] = True
            
        nonce_counter = context["nonce_counter"]
        nonce = context["master_nonce"] + struct.pack(">I", nonce_counter)
        
        # Encrypt
        ciphertext_with_tag = self.aes_gcm.encrypt(nonce, chunk, None)
        tag = ciphertext_with_tag[-16:]
        ciphertext = ciphertext_with_tag[:-16]
        
        # Pack chunk
        chunk_header = struct.pack(self.CHUNK_HEADER_STRUCT, len(ciphertext), nonce_counter, tag)
        result += chunk_header + ciphertext
        
        context["nonce_counter"] += 1
        return result

    def get_encrypted_chunk_size(self, chunk_size: int) -> int:
        """Calculate the size of an encrypted chunk. 
        Note: This is now used for both GCM and Fernet (backward compatibility).
        For GCM, it adds CHUNK_HEADER_SIZE.
        """
        # If we are in GCM mode, the overhead is fixed per chunk.
        return chunk_size + self.CHUNK_HEADER_SIZE

    async def decrypt_stream_async(self, encrypted_stream):
        """Asynchronous generator to decrypt a stream of encrypted data."""
        buffer = b""
        header_parsed = False
        master_nonce = None
        
        async for encrypted_chunk in encrypted_stream:
            buffer += encrypted_chunk
            
            if not header_parsed:
                if len(buffer) < self.HEADER_SIZE:
                    continue
                header_data = buffer[:self.HEADER_SIZE]
                if header_data.startswith(self.GCM_MAGIC):
                    magic, version, def_chunk_size, master_nonce = struct.unpack(self.HEADER_STRUCT, header_data)
                    if version != 2:
                        raise ValueError(f"Unsupported GCM version: {version}")
                    buffer = buffer[self.HEADER_SIZE:]
                    header_parsed = True
                else:
                    # Not our magic. If we want to support streaming Fernet, we'd need a different approach.
                    # For now, let's assume it's GCM if we are using this method.
                    raise ValueError("Invalid magic - not a GCM encrypted stream")
            
            # Process chunks
            while len(buffer) >= self.CHUNK_HEADER_SIZE:
                c_len, nonce_counter, tag = struct.unpack(self.CHUNK_HEADER_STRUCT, buffer[:self.CHUNK_HEADER_SIZE])
                
                needed = self.CHUNK_HEADER_SIZE + c_len
                if len(buffer) < needed:
                    break
                
                # We have a full chunk
                ciphertext = buffer[self.CHUNK_HEADER_SIZE : needed]
                buffer = buffer[needed:]
                
                nonce = master_nonce + struct.pack(">I", nonce_counter)
                decrypted = self.aes_gcm.decrypt(nonce, ciphertext + tag, None)
                yield decrypted

            
            if header_parsed:
                # Process GCM chunks
                while len(buffer) >= self.CHUNK_HEADER_SIZE:
                    chunk_header = buffer[:self.CHUNK_HEADER_SIZE]
                    nonce_counter, tag = struct.unpack(self.CHUNK_HEADER_STRUCT, chunk_header)
                    
                    # We need to know how much ciphertext to read.
                    # For all but the last chunk, it's `chunk_size`.
                    # But we don't know if this is the last chunk yet!
                    # Actually, if we have more data after `chunk_size` bytes, then it's definitely not the last one OR it's the last one and that's it.
                    
                    needed = self.CHUNK_HEADER_SIZE + chunk_size
                    if len(buffer) < needed:
                        # Need more data to decrypt this chunk
                        # Wait, what if it's the LAST chunk and it's smaller than chunk_size?
                        # We don't know the size of the last chunk from the header!
                        # This is a flaw in my design. 
                        # I should probably include the ciphertext length in the chunk header if it can be variable.
                        break
                    
                    # If we have enough data for a full chunk, process it.
                    # But wait, what if the last chunk is exactly chunk_size?
                    # Or what if it's smaller?
                    
                    # Let's check if there's any data left after this chunk.
                    # If we have exactly `needed` bytes, it MIGHT be the last chunk.
                    
                    # Actually, in GCM, we know the ciphertext length is the same as plaintext.
                    # Let's adjust the format to include ciphertext length in chunk header.
                    pass
        
        # ... (I'll rethink the format)




# Global encryption service instance
encryption_service = EncryptionService()