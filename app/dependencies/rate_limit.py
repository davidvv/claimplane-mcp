"""Rate limiting dependency using slowapi."""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import config

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
    storage_uri=config.REDIS_URL,  # Use Redis for shared state across processes
    headers_enabled=True  # Enable rate limit headers in responses
)
