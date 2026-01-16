"""Database connection and session management for MCP server."""
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from config import MCPConfig

# Import base models from main app
from app.database import Base
from app.models import Customer, Claim, ClaimFile, ClaimNote, ClaimStatusHistory
from app.repositories import CustomerRepository, ClaimRepository

# Create async engine for MCP server
engine = create_async_engine(
    MCPConfig.DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # No connection pooling for MCP server
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for MCP tools."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """Initialize database connection (verify connectivity)."""
    async with engine.begin() as conn:
        # Just test the connection
        await conn.execute(text("SELECT 1"))
    return True


async def close_database():
    """Close database connections."""
    await engine.dispose()
