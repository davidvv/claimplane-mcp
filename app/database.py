"""Database configuration and session management."""
import os
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import MetaData

logger = logging.getLogger(__name__)


def _get_database_url() -> str:
    """Get database URL with security validation."""
    url = os.getenv("DATABASE_URL")
    
    if not url:
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "production":
            raise ValueError(
                "CRITICAL: DATABASE_URL environment variable must be set in production. "
                "Example: postgresql+asyncpg://user:password@host:5432/database"
            )
        
        logger.warning(
            "DATABASE_URL not set - using development default. "
            "Set DATABASE_URL environment variable for proper configuration."
        )
        # Development default with placeholder to force explicit configuration
        return "postgresql+asyncpg://postgres:postgres@localhost:5432/flight_claim"
    
    return url


# Database URL from environment variable
DATABASE_URL = _get_database_url()

# Create async engine
# SECURITY: SQL echo disabled by default in production to prevent query logging
import os
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"
engine = create_async_engine(
    DATABASE_URL,
    echo=SQL_ECHO,
    future=True,
    # SECURITY: Hide parameters in production to prevent sensitive data in logs
    hide_parameters=os.getenv("ENVIRONMENT") == "production"
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create declarative base
Base = declarative_base()

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

Base.metadata = MetaData(naming_convention=convention)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db(confirm: bool = False):
    """
    Drop all database tables.
    
    DANGEROUS: This will permanently delete all data!
    
    Args:
        confirm: Must be True to execute. Prevents accidental calls.
    
    Raises:
        RuntimeError: If called in production or without confirmation.
    """
    # Prevent execution in production
    if os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError(
            "CRITICAL: drop_db() cannot be called in production environment. "
            "This would result in catastrophic data loss."
        )
    
    # Require explicit confirmation
    if not confirm:
        raise RuntimeError(
            "drop_db() requires confirm=True to execute. "
            "This is a safety measure to prevent accidental data loss."
        )
    
    logger.warning("DROPPING ALL DATABASE TABLES - This action cannot be undone!")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.warning("All database tables have been dropped.")