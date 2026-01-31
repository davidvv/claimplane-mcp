import hashlib
import hmac
import base64
from app.config import config

def get_encryption_key():
    """Get the database encryption key."""
    return config.DB_ENCRYPTION_KEY

def _get_blind_index_key():
    """Derive a specific key for blind indexing from the main encryption key."""
    # We derive a separate key so that knowledge of the search index hashes 
    # doesn't directly reveal the encryption key, although in this config 
    # the root secret is the same.
    return hashlib.sha256(config.DB_ENCRYPTION_KEY.encode()).digest()

def generate_blind_index(value: str | None) -> str | None:
    """
    Generate a deterministic hash (Blind Index) for searching encrypted fields.
    
    This allows exact-match searching (WHERE email_idx = '...') without 
    exposing the plaintext data.
    
    Args:
        value: The plaintext value to index (e.g. email, PNR)
        
    Returns:
        Base64 encoded HMAC-SHA256 hash of the normalized value
    """
    if value is None:
        return None
    
    # Normalize input (lowercase, strip whitespace) to ensure case-insensitive match
    # Note: This means all searches must also be normalized before querying
    normalized = str(value).lower().strip()
    
    # Generate HMAC-SHA256
    # We use HMAC instead of simple SHA256 to prevent rainbow table attacks
    h = hmac.new(_get_blind_index_key(), normalized.encode(), hashlib.sha256)
    
    return base64.b64encode(h.digest()).decode()
