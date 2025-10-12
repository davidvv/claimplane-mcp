"""Configuration management for secure secrets."""
import os
import secrets
from typing import Optional
from cryptography.fernet import Fernet


class SecureConfig:
    """Secure configuration management with proper secret handling."""
    
    @staticmethod
    def generate_encryption_key() -> str:
        """Generate a secure encryption key."""
        return Fernet.generate_key().decode()
    
    @staticmethod
    def generate_secure_password(length: int = 32) -> str:
        """Generate a secure password."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_jwt_secret(length: int = 64) -> str:
        """Generate a secure JWT secret."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def get_required_env_var(var_name: str, default: Optional[str] = None) -> str:
        """Get required environment variable with proper error handling."""
        value = os.getenv(var_name, default)
        if not value:
            raise ValueError(f"Required environment variable {var_name} is not set")
        return value
    
    @staticmethod
    def validate_encryption_key(key: str) -> bool:
        """Validate that the encryption key is properly formatted."""
        try:
            # Try to create a Fernet instance with the key
            Fernet(key.encode() if isinstance(key, str) else key)
            return True
        except Exception:
            return False


# Production-ready configuration with secure defaults
class Config:
    """Application configuration with secure defaults."""
    
    # Database Configuration
    DATABASE_URL = SecureConfig.get_required_env_var(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@db:5432/flight_claim"
    )
    
    # Security Configuration
    SECRET_KEY = SecureConfig.get_required_env_var(
        "SECRET_KEY",
        SecureConfig.generate_jwt_secret()
    )
    
    # File Management Configuration
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 50MB
    FILE_ENCRYPTION_KEY = SecureConfig.get_required_env_var(
        "FILE_ENCRYPTION_KEY",
        SecureConfig.generate_encryption_key()
    )

    # Streaming Configuration for Large Files
    STREAMING_THRESHOLD = int(os.getenv("STREAMING_THRESHOLD", "52428800"))  # 50MB
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "8388608"))  # 8MB
    MAX_MEMORY_BUFFER = int(os.getenv("MAX_MEMORY_BUFFER", "104857600"))  # 100MB
    
    # Validate encryption key
    if not SecureConfig.validate_encryption_key(FILE_ENCRYPTION_KEY):
        raise ValueError("Invalid FILE_ENCRYPTION_KEY format. Must be a valid Fernet key.")
    
    # Nextcloud Configuration (should be set in production)
    NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL", "http://localhost:8081")
    NEXTCLOUD_USERNAME = os.getenv("NEXTCLOUD_USERNAME", "admin")
    NEXTCLOUD_PASSWORD = os.getenv("NEXTCLOUD_PASSWORD", "admin_secure_password_2024")
    
    # Redis Configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Security Settings
    VIRUS_SCAN_ENABLED = os.getenv("VIRUS_SCAN_ENABLED", "true").lower() == "true"
    CLAMAV_URL = os.getenv("CLAMAV_URL", "clamav:3310")
    
    # Rate Limiting
    RATE_LIMIT_UPLOAD = os.getenv("RATE_LIMIT_UPLOAD", "10/minute")
    RATE_LIMIT_DOWNLOAD = os.getenv("RATE_LIMIT_DOWNLOAD", "100/minute")
    
    # JWT Configuration
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "30"))
    JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8081").split(",")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # API Configuration
    API_VERSION = os.getenv("API_VERSION", "1.0.0")
    API_TITLE = os.getenv("API_TITLE", "Flight Claim System API")
    
    # Security Headers
    SECURITY_HEADERS_ENABLED = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
    
    # File Retention
    FILE_RETENTION_DAYS = int(os.getenv("FILE_RETENTION_DAYS", "365"))
    
    # Nextcloud Settings
    NEXTCLOUD_TIMEOUT = int(os.getenv("NEXTCLOUD_TIMEOUT", "30"))
    NEXTCLOUD_MAX_RETRIES = int(os.getenv("NEXTCLOUD_MAX_RETRIES", "3"))

    # Post-Upload Verification Configuration
    UPLOAD_VERIFICATION_ENABLED = os.getenv("UPLOAD_VERIFICATION_ENABLED", "true").lower() == "true"
    VERIFICATION_TIMEOUT = int(os.getenv("VERIFICATION_TIMEOUT", "300"))  # 5 minutes
    VERIFICATION_MAX_RETRIES = int(os.getenv("VERIFICATION_MAX_RETRIES", "3"))
    VERIFICATION_MAX_FILE_SIZE = int(os.getenv("VERIFICATION_MAX_FILE_SIZE", "1073741824"))  # 1GB
    VERIFICATION_MIN_FILE_SIZE = int(os.getenv("VERIFICATION_MIN_FILE_SIZE", "1024"))  # 1KB
    VERIFICATION_CHUNK_SIZE = int(os.getenv("VERIFICATION_CHUNK_SIZE", "1048576"))  # 1MB for comparison
    VERIFICATION_SAMPLE_SIZE = int(os.getenv("VERIFICATION_SAMPLE_SIZE", "10485760"))  # 10MB for sampling
    VERIFICATION_RETRY_DELAY = int(os.getenv("VERIFICATION_RETRY_DELAY", "5"))  # seconds


# Development configuration with relaxed security
class DevelopmentConfig(Config):
    """Development configuration with relaxed security for testing."""
    
    # Allow more permissive settings in development
    CORS_ORIGINS = ["*"]
    RATE_LIMIT_UPLOAD = "100/minute"
    RATE_LIMIT_DOWNLOAD = "1000/minute"
    SECURITY_HEADERS_ENABLED = False


# Production configuration with strict security
class ProductionConfig(Config):
    """Production configuration with strict security settings."""
    
    # Strict security settings
    CORS_ORIGINS = SecureConfig.get_required_env_var("CORS_ORIGINS", "https://yourdomain.com").split(",")
    RATE_LIMIT_UPLOAD = "5/minute"
    RATE_LIMIT_DOWNLOAD = "50/minute"
    SECURITY_HEADERS_ENABLED = True
    
    # Force secure settings in production
    @classmethod
    def validate_production_settings(cls):
        """Validate that production settings are secure."""
        if cls.NEXTCLOUD_PASSWORD == "admin":
            raise ValueError("NEXTCLOUD_PASSWORD must be changed from default for production")
        
        if cls.FILE_ENCRYPTION_KEY == SecureConfig.generate_encryption_key():
            raise ValueError("FILE_ENCRYPTION_KEY must be explicitly set for production")
        
        if not cls.SECURITY_HEADERS_ENABLED:
            raise ValueError("SECURITY_HEADERS_ENABLED must be true for production")


# Configuration factory
def get_config(environment: str = None) -> Config:
    """Get configuration based on environment."""
    env = environment or os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        config = ProductionConfig
        config.validate_production_settings()
        return config
    elif env == "development":
        return DevelopmentConfig
    else:
        return Config


# Export the current configuration
config = get_config()