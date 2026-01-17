"""Pytest configuration and shared fixtures for tests."""
import pytest
import pytest_asyncio
import os
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import Base, get_db
from app.models import Customer
from app.services.auth_service import AuthService
from app.config import config

# Test database URL (using same credentials as main database)
# Allow overriding via environment variable (e.g. for Docker)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/test_flight_claim"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden database dependency."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_customer(db_session: AsyncSession) -> Customer:
    """Create a test customer."""
    customer = await AuthService.register_user(
        session=db_session,
        email="test@example.com",
        password="TestPassword123!",
        first_name="Test",
        last_name="Customer",
        phone="+1234567890"
    )
    await db_session.commit()
    await db_session.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> Customer:
    """Create a test admin user."""
    admin = await AuthService.register_user(
        session=db_session,
        email="admin@example.com",
        password="AdminPassword123!",
        first_name="Admin",
        last_name="User",
        phone="+1234567891"
    )
    admin.role = Customer.ROLE_ADMIN
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def test_superadmin(db_session: AsyncSession) -> Customer:
    """Create a test superadmin user."""
    superadmin = await AuthService.register_user(
        session=db_session,
        email="superadmin@example.com",
        password="SuperPassword123!",
        first_name="Super",
        last_name="Admin",
        phone="+1234567892"
    )
    superadmin.role = Customer.ROLE_SUPERADMIN
    await db_session.commit()
    await db_session.refresh(superadmin)
    return superadmin


@pytest_asyncio.fixture
def customer_token(test_customer: Customer) -> str:
    """Generate JWT token for test customer."""
    return AuthService.create_access_token(
        user_id=test_customer.id,
        email=test_customer.email,
        role=test_customer.role
    )


@pytest_asyncio.fixture
def admin_token(test_admin: Customer) -> str:
    """Generate JWT token for test admin."""
    return AuthService.create_access_token(
        user_id=test_admin.id,
        email=test_admin.email,
        role=test_admin.role
    )


@pytest_asyncio.fixture
def superadmin_token(test_superadmin: Customer) -> str:
    """Generate JWT token for test superadmin."""
    return AuthService.create_access_token(
        user_id=test_superadmin.id,
        email=test_superadmin.email,
        role=test_superadmin.role
    )


@pytest.fixture
def auth_headers(customer_token: str) -> dict:
    """Create authorization headers for test customer."""
    return {"Authorization": f"Bearer {customer_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """Create authorization headers for test admin."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def superadmin_headers(superadmin_token: str) -> dict:
    """Create authorization headers for test superadmin."""
    return {"Authorization": f"Bearer {superadmin_token}"}
