"""Request utility functions."""
from typing import Optional, Tuple
from fastapi import Request

def get_real_ip(request: Request) -> str:
    """
    Get the real client IP address, accounting for Cloudflare tunnel and other proxies.

    Cloudflare adds these headers:
    - CF-Connecting-IP: The original client IP
    - X-Forwarded-For: Chain of proxy IPs
    """
    # Trust Cloudflare's CF-Connecting-IP header first
    # We use capitalized names for standard headers, but FastAPI handles them case-insensitively
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip

    # Fallback to X-Forwarded-For (first IP in chain)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Fallback to X-Real-IP
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    # Fallback to direct connection IP
    if request.client:
        return request.client.host
    
    return "unknown"

def get_client_info(request: Request) -> Tuple[str, str]:
    """
    Extract real client IP and user agent from request.
    
    Returns:
        tuple: (ip_address, user_agent)
    """
    ip_address = get_real_ip(request)
    user_agent = request.headers.get("user-agent", "unknown")
    return ip_address, user_agent
