"""Rate limiting dependency using slowapi."""
from fastapi import Request
from slowapi import Limiter
from app.utils.request_utils import get_real_ip
from app.config import config

# Create rate limiter
limiter = Limiter(
    key_func=get_real_ip,
    default_limits=["100/minute"],  # Global default
    storage_uri=config.REDIS_URL,  # Use Redis for shared state across processes
    headers_enabled=True  # Enable rate limit headers in responses
)
