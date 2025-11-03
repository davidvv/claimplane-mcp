"""Dependencies for FastAPI endpoints."""
from app.dependencies.auth import (
    get_current_user,
    get_current_active_user,
    get_current_verified_user,
    get_current_admin,
    get_current_superadmin,
    get_optional_current_user,
    require_role,
)

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_current_verified_user",
    "get_current_admin",
    "get_current_superadmin",
    "get_optional_current_user",
    "require_role",
]
