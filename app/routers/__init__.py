"""Routers package for the flight claim application."""
from .health import router as health_router
from .customers import router as customers_router
from .claims import router as claims_router
from .files import router as files_router

__all__ = [
    "health_router",
    "customers_router", 
    "claims_router",
    "files_router"
]