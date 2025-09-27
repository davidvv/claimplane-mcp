"""Repository pattern implementation for data access."""
from .customer_repository import CustomerRepository
from .claim_repository import ClaimRepository

__all__ = ["CustomerRepository", "ClaimRepository"]