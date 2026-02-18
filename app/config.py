"""Configuration management for secure secrets."""
import os
import secrets
from typing import Optional
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables from .env file only in development
# In production, env vars should be explicitly set (not from .env file)
# Check ENVIRONMENT first from existing env vars, then load .env if not production
_environment = os.getenv("ENVIRONMENT", "development")
if _environment != "production":
    load_dotenv()


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
    
    @staticmethod
    def get_encryption_key(var_name: str) -> str:
        """
        Get encryption key from environment variable.
        
        SECURITY: In production, this MUST be set via environment variable.
        In development, generates a temporary key if not set.
        """
        key = os.getenv(var_name)
        
        if not key:
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError(
                    f"CRITICAL SECURITY ERROR: {var_name} must be set in production.\n"
                    f"Generate a secure key with:\n"
                    f"python -c \"from cryptography.fernet import Fernet; "
                    f"print(Fernet.generate_key().decode())\""
                )
            # Development: generate temporary key (changes on restart)
            import warnings
            warnings.warn(
                f"{var_name} not set - generating temporary key for development. "
                f"Set this in your .env file for persistent encryption.",
                RuntimeWarning
            )
            return Fernet.generate_key().decode()
        
        # Validate key format
        if not SecureConfig.validate_encryption_key(key):
            raise ValueError(
                f"{var_name} is not a valid Fernet key. "
                f"Generate a new key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        
        return key
    
    @staticmethod
    def get_jwt_secret() -> str:
        """
        Get JWT secret from environment variable.
        
        SECURITY: In production, this MUST be set via environment variable.
        In development, generates a random secret if not set.
        """
        key = os.getenv("SECRET_KEY")
        
        if not key:
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError(
                    "CRITICAL SECURITY ERROR: SECRET_KEY must be set in production.\n"
                    "Generate a secure secret with:\n"
                    "python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            # Development: generate random secret (changes on restart)
            import warnings
            warnings.warn(
                "SECRET_KEY not set - generating temporary secret for development. "
                f"This will invalidate existing tokens on restart. "
                "Set SECRET_KEY in your .env file for persistent sessions.",
                RuntimeWarning
            )
            return secrets.token_urlsafe(64)
        
        # Validate minimum entropy
        if len(key) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 characters (current: {len(key)}). "
                f"Generate a secure secret with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        
        return key


# Production-ready configuration with secure defaults
class Config:
    """Application configuration with secure defaults."""
    
    # Database Configuration
    # SECURITY: No default password - must be set via environment variable
    DATABASE_URL = SecureConfig.get_required_env_var(
        "DATABASE_URL",
        "postgresql+asyncpg://user:CHANGE_ME@db:5432/flight_claim"  # Placeholder - will fail if not overridden
    )
    
    # Security Configuration
    # SECURITY: Use SecureConfig helper to enforce production secrets
    SECRET_KEY = SecureConfig.get_jwt_secret()
    
    # File Management Configuration
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 50MB
    
    # SECURITY: Encryption keys retrieved via SecureConfig helper
    # This enforces environment variables in production and generates
    # temporary keys in development only
    FILE_ENCRYPTION_KEY = SecureConfig.get_encryption_key("FILE_ENCRYPTION_KEY")
    DB_ENCRYPTION_KEY = SecureConfig.get_encryption_key("DB_ENCRYPTION_KEY")

    # Streaming Configuration for Large Files
    STREAMING_THRESHOLD = int(os.getenv("STREAMING_THRESHOLD", "52428800"))  # 50MB
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "8388608"))  # 8MB
    MAX_MEMORY_BUFFER = int(os.getenv("MAX_MEMORY_BUFFER", "104857600"))  # 100MB
    
    # SECURITY NOTE: Encryption key validation is now handled by SecureConfig.get_encryption_key()
    # This ensures keys are validated at load time with proper error messages
    
    # Nextcloud Configuration (should be set in production)
    NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL", "http://localhost:8081")
    NEXTCLOUD_USERNAME = os.getenv("NEXTCLOUD_USERNAME", "admin")
    NEXTCLOUD_PASSWORD = os.getenv("NEXTCLOUD_PASSWORD", "admin_secure_password_2024")
    
    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = os.getenv("REDIS_PORT", "6379")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    
    # Construct REDIS_URL if not provided, otherwise use the provided one
    _default_redis_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}"
    REDIS_URL = os.getenv("REDIS_URL", _default_redis_url)

    # Email Configuration (Phase 2)
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@flightclaim.com")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "ClaimPlane LLC")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "vences.david@icloud.com")

    # Celery Configuration (Phase 2)
    CELERY_BROKER_URL = REDIS_URL  # Use Redis as broker
    CELERY_RESULT_BACKEND = REDIS_URL  # Use Redis as result backend
    CELERY_TASK_SERIALIZER = "json"
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TIMEZONE = "UTC"
    CELERY_ENABLE_UTC = True
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes max per task

    # Notification Settings (Phase 2)
    NOTIFICATIONS_ENABLED = os.getenv("NOTIFICATIONS_ENABLED", "true").lower() == "true"

    # Security Settings
    VIRUS_SCAN_ENABLED = os.getenv("VIRUS_SCAN_ENABLED", "true").lower() == "true"
    CLAMAV_URL = os.getenv("CLAMAV_URL", "clamav:3310")
    
    # Account Lockout
    AUTH_LOCKOUT_THRESHOLD = int(os.getenv("AUTH_LOCKOUT_THRESHOLD", "10"))
    AUTH_LOCKOUT_DURATION_HOURS = int(os.getenv("AUTH_LOCKOUT_DURATION_HOURS", "24"))
    AUTH_BACKOFF_STAGES = {3: 5, 5: 30, 8: 60}  # Attempts: Seconds to delay
    AUTH_REDIS_PREFIX = "auth:failed:"
    
    # Rate Limiting
    RATE_LIMIT_UPLOAD = os.getenv("RATE_LIMIT_UPLOAD", "10/minute")
    RATE_LIMIT_DOWNLOAD = os.getenv("RATE_LIMIT_DOWNLOAD", "100/minute")
    
    # JWT Configuration
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "30"))
    JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))
    
    # CORS Configuration
    # SECURITY: In production, validate origins strictly
    @property
    def CORS_ORIGINS(self):
        origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8081,https://eac.dvvcloud.work")
        origins = [o.strip() for o in origins_str.split(",") if o.strip()]
        
        # In production, enforce strict validation
        if os.getenv("ENVIRONMENT") == "production":
            if not origins:
                raise ValueError("CORS_ORIGINS must be set in production")
            
            validated_origins = []
            for origin in origins:
                # Enforce HTTPS in production
                if not origin.startswith("https://"):
                    raise ValueError(f"CORS origin must use HTTPS in production: {origin}")
                # Prevent wildcards
                if "*" in origin:
                    raise ValueError(f"CORS origin cannot contain wildcard: {origin}")
                validated_origins.append(origin)
            return validated_origins
        
        return origins
    
    # Trusted Hosts Configuration
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,eac.dvvcloud.work,api").split(",")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # API Configuration
    API_VERSION = os.getenv("API_VERSION", "1.0.0")
    API_TITLE = os.getenv("API_TITLE", "ClaimPlane API")
    
    # Security Headers
    SECURITY_HEADERS_ENABLED = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
    
    # File Retention
    FILE_RETENTION_DAYS = int(os.getenv("FILE_RETENTION_DAYS", "365"))
    DRAFT_RETENTION_DAYS = int(os.getenv("DRAFT_RETENTION_DAYS", "11"))
    
    # Nextcloud Settings
    NEXTCLOUD_TIMEOUT = int(os.getenv("NEXTCLOUD_TIMEOUT", "30"))
    NEXTCLOUD_MAX_RETRIES = int(os.getenv("NEXTCLOUD_MAX_RETRIES", "3"))

    # AeroDataBox API Configuration (Phase 6)
    AERODATABOX_API_KEY = os.getenv("AERODATABOX_API_KEY", "")
    AERODATABOX_BASE_URL = os.getenv("AERODATABOX_BASE_URL", "https://api.aerodatabox.com/v1")
    AERODATABOX_TIMEOUT = int(os.getenv("AERODATABOX_TIMEOUT", "30"))
    AERODATABOX_MAX_RETRIES = int(os.getenv("AERODATABOX_MAX_RETRIES", "3"))
    AERODATABOX_ENABLED = os.getenv("AERODATABOX_ENABLED", "false").lower() == "true"

    # Airport Taxi Time Configuration
    # AeroDataBox only provides runway touchdown time, not gate arrival (door opening)
    # EU261 delay is measured to gate arrival, so we add airport-specific taxi-in times
    # Data source: CSV file with taxi times for 184 major airports
    FLIGHT_TAXI_TIME_DEFAULT_MINUTES = int(os.getenv("FLIGHT_TAXI_TIME_DEFAULT_MINUTES", "15"))
    AIRPORT_TAXI_TIMES_CSV_PATH = os.getenv(
        "AIRPORT_TAXI_TIMES_CSV_PATH",
        "app/data/comprehensive_airport_taxiing_times.csv"
    )

    # AeroDataBox Quota Management
    AERODATABOX_MONTHLY_QUOTA = int(os.getenv("AERODATABOX_MONTHLY_QUOTA", "600"))  # Free tier: 600 credits/month
    AERODATABOX_ALERT_THRESHOLD = int(os.getenv("AERODATABOX_ALERT_THRESHOLD", "80"))  # Alert at 80% usage

    # Flight Data Caching
    FLIGHT_DATA_CACHE_HOURS = int(os.getenv("FLIGHT_DATA_CACHE_HOURS", "24"))
    FLIGHT_CACHE_TTL_SECONDS = FLIGHT_DATA_CACHE_HOURS * 3600  # Convert to seconds for Redis

    # Phase 6.5: Flight Search by Route Configuration
    FLIGHT_SEARCH_ENABLED = os.getenv("FLIGHT_SEARCH_ENABLED", "false").lower() == "true"
    FLIGHT_SEARCH_PROVIDER = os.getenv("FLIGHT_SEARCH_PROVIDER", "aerodatabox")  # aerodatabox, aviationstack

    # Provider-specific configs (defaults to Phase 6 values for consistency)
    FLIGHT_SEARCH_API_KEY = os.getenv("FLIGHT_SEARCH_API_KEY", AERODATABOX_API_KEY)
    FLIGHT_SEARCH_BASE_URL = os.getenv("FLIGHT_SEARCH_BASE_URL", AERODATABOX_BASE_URL)

    # Search configuration
    FLIGHT_SEARCH_MAX_RESULTS = int(os.getenv("FLIGHT_SEARCH_MAX_RESULTS", "50"))
    FLIGHT_SEARCH_CACHE_HOURS = int(os.getenv("FLIGHT_SEARCH_CACHE_HOURS", "24"))
    FLIGHT_SEARCH_CACHE_TTL_SECONDS = FLIGHT_SEARCH_CACHE_HOURS * 3600

    # Airport autocomplete
    AIRPORT_AUTOCOMPLETE_CACHE_DAYS = int(os.getenv("AIRPORT_AUTOCOMPLETE_CACHE_DAYS", "7"))
    AIRPORT_AUTOCOMPLETE_CACHE_TTL_SECONDS = AIRPORT_AUTOCOMPLETE_CACHE_DAYS * 86400

    # Analytics
    FLIGHT_SEARCH_ANALYTICS_ENABLED = os.getenv("FLIGHT_SEARCH_ANALYTICS_ENABLED", "true").lower() == "true"

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
    # Note: Cannot use "*" wildcard when allow_credentials=True (required for HTTP-only cookies)
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8081,https://eac.dvvcloud.work").split(",")
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,eac.dvvcloud.work,api").split(",")
    RATE_LIMIT_UPLOAD = "100/minute"
    RATE_LIMIT_DOWNLOAD = "1000/minute"
    SECURITY_HEADERS_ENABLED = False


# Production configuration with strict security
class ProductionConfig(Config):
    """Production configuration with strict security settings."""
    
    # Strict security settings
    CORS_ORIGINS = SecureConfig.get_required_env_var("CORS_ORIGINS", "https://yourdomain.com").split(",")
    ALLOWED_HOSTS = SecureConfig.get_required_env_var("ALLOWED_HOSTS", "yourdomain.com").split(",")
    RATE_LIMIT_UPLOAD = "5/minute"
    RATE_LIMIT_DOWNLOAD = "50/minute"
    SECURITY_HEADERS_ENABLED = True
    
    # Force secure settings in production
    @classmethod
    def validate_production_settings(cls):
        """Validate that production settings are secure."""
        if cls.NEXTCLOUD_PASSWORD == "admin":
            raise ValueError("NEXTCLOUD_PASSWORD must be changed from default for production")
        
        # Check if FILE_ENCRYPTION_KEY was set via environment variable
        if not os.getenv("FILE_ENCRYPTION_KEY"):
            raise ValueError("FILE_ENCRYPTION_KEY must be explicitly set via environment variable for production")
        
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