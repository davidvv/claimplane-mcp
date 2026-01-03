"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import engine, Base
from app.routers import health, customers, claims, files, admin_claims, admin_files, admin_deletion_requests, eligibility, auth, flights, account
from app.exceptions import setup_exception_handlers
from app.config import get_config

# Get configuration
config = get_config()

# Rate limiting - Get real IP from Cloudflare headers
def get_real_ip(request: Request) -> str:
    """
    Get the real client IP address, accounting for Cloudflare tunnel.

    Cloudflare adds these headers:
    - CF-Connecting-IP: The original client IP
    - X-Forwarded-For: Chain of proxy IPs
    """
    # Trust Cloudflare's CF-Connecting-IP header first
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip

    # Fallback to X-Forwarded-For (first IP in chain)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # Fallback to direct connection IP
    return get_remote_address(request)

# Create rate limiter
limiter = Limiter(
    key_func=get_real_ip,
    default_limits=["100/minute"],  # Global default
    storage_uri="memory://",  # Use Redis in production: "redis://redis:6379"
    headers_enabled=True  # Enable rate limit headers in responses
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Flight Claim System API...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created successfully")

    # Load airport taxi times for accurate EU261 delay calculations
    from app.services.airport_taxi_time_service import AirportTaxiTimeService
    try:
        AirportTaxiTimeService.load_taxi_times(config.AIRPORT_TAXI_TIMES_CSV_PATH)
        airport_count = AirportTaxiTimeService.get_airport_count()
        logger.info(f"Airport taxi times loaded successfully ({airport_count} airports)")
    except Exception as e:
        logger.warning(
            f"Failed to load airport taxi times: {e}. "
            f"Will use default {config.FLIGHT_TAXI_TIME_DEFAULT_MINUTES} min fallback."
        )

    yield

    # Shutdown
    logger.info("Shutting down Flight Claim System API...")


# Create FastAPI app
app = FastAPI(
    title="Flight Claim System API",
    description="API for managing flight compensation claims with file management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    redirect_slashes=False  # Disable automatic slash redirects to avoid CORS issues
)

# Add rate limiting state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Setup CORS - Use config to prevent wildcard with credentials vulnerability
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,  # No longer uses wildcard ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Setup exception handlers
setup_exception_handlers(app)


# Include routers
app.include_router(health.router)
app.include_router(auth.router)  # Phase 3: Authentication
app.include_router(account.router)  # Phase 4: Account Management
app.include_router(flights.router)  # Mock flight lookup
app.include_router(eligibility.router)

app.include_router(customers.router)
app.include_router(claims.router)
app.include_router(files.router)

# Admin routers (Phase 1)
app.include_router(admin_claims.router)
app.include_router(admin_files.router)
app.include_router(admin_deletion_requests.router)  # Phase 4: Deletion Request Management


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Flight Claim System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/info")
async def info():
    """API information endpoint."""
    return {
        "name": "Flight Claim System API",
        "version": "1.0.0",
        "description": "API for managing flight compensation claims with file management",
        "environment": "development",
        "features": [
            "Customer management",
            "Claim submission and tracking",
            "Flight incident reporting",
            "File management with Nextcloud integration",
            "Secure file uploads with encryption",
            "Document validation and scanning",
            "Admin claim management and workflow (Phase 1)",
            "EU261/2004 compensation calculation",
            "Document review and approval system",
            "Bulk operations and analytics",
            "Public eligibility check endpoint (no auth required)",
            "JWT-based authentication (Phase 3)",
            "User registration and login",
            "Password reset flow",
            "Role-based access control (RBAC)",
            "Email verification support"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )