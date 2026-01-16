"""Configuration for EasyAirClaim MCP Server."""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add main app to Python path to import models/services
MAIN_APP_PATH = os.getenv("MAIN_APP_PATH", "/home/david/easyAirClaim/easyAirClaim")
sys.path.insert(0, MAIN_APP_PATH)


class MCPConfig:
    """MCP Server Configuration."""
    
    # Environment Safety Check
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    if ENVIRONMENT == "production":
        raise RuntimeError(
            "⚠️  MCP SERVER CANNOT RUN IN PRODUCTION!\n"
            "   This server has full database access and no authentication.\n"
            "   Set ENVIRONMENT=development to proceed."
        )
    
    # MCP Server Settings
    MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT = int(os.getenv("MCP_PORT", "39128"))
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8083"))
    
    # Database Connection (from main app)
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/flight_claim"
    )
    
    # Main App Path
    APP_PATH = MAIN_APP_PATH
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Development Features
    ENABLE_DESTRUCTIVE_OPS = os.getenv("ENABLE_DESTRUCTIVE_OPS", "true").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Validate critical configuration."""
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set")
        
        if cls.ENVIRONMENT == "production":
            raise RuntimeError("MCP server is for development only!")
        
        return True


# Validate on import
MCPConfig.validate()
