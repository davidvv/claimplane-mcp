"""Configuration settings for the Easy Air Claim API."""

import os
from typing import List, Optional

from pydantic import EmailStr
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Application
    app_name: str = "Easy Air Claim API"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str
    database_test_url: Optional[str] = None
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # File Upload
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 5
    allowed_file_types: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/jpg",
        "image/png"
    ]
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # Email
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[EmailStr] = None
    
    # Admin
    admin_email: EmailStr
    admin_password: str
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def assemble_allowed_file_types(cls, v):
        """Parse allowed file types from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return cls.model_fields["allowed_file_types"].default
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()