import os
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


def key_func_with_user(request) -> str:
    """Use client IP address as the rate limit key (no auth)."""
    return get_remote_address(request)


def key_func_analysis_endpoint(request) -> str:
    """Rate limiting key for analysis endpoint - more restrictive"""
    client_ip = get_remote_address(request)
    return f"analysis:{client_ip}"


def key_func_export_endpoint(request) -> str:
    """Rate limiting key for export endpoint"""
    client_ip = get_remote_address(request)
    return f"export:{client_ip}"


def key_func_auth_endpoint(request) -> str:
    """Rate limiting key for auth endpoints - very restrictive"""
    client_ip = get_remote_address(request)
    return f"auth:{client_ip}"


# Rate limiting configuration
default_limit = os.getenv("RATE_LIMIT_DEFAULT", "100 per minute")
analysis_limit = os.getenv("RATE_LIMIT_ANALYSIS", "10 per minute")
export_limit = os.getenv("RATE_LIMIT_EXPORT", "20 per minute")
auth_limit = os.getenv("RATE_LIMIT_AUTH", "5 per minute")

storage_uri = os.getenv("RATE_LIMIT_STORAGE_URI")  # e.g., redis://localhost:6379

# Make Redis optional - use in-memory storage if no Redis URL provided
if not storage_uri:
    storage_uri = "memory://"
    logger.info("Using in-memory rate limiting storage")

# Test Redis connection if provided
if storage_uri.startswith("redis://"):
    try:
        import redis

        redis_client = redis.from_url(storage_uri, decode_responses=True)
        redis_client.ping()
        logger.info("Redis connection established for rate limiting")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Using in-memory rate limiting")
        storage_uri = "memory://"

# Default limiter for general endpoints
limiter = Limiter(
    key_func=key_func_with_user,
    default_limits=[default_limit],
    storage_uri=storage_uri,
)

# Analysis endpoint limiter - more restrictive
analysis_limiter = Limiter(
    key_func=key_func_analysis_endpoint,
    default_limits=[analysis_limit],
    storage_uri=storage_uri,
)

# Export endpoint limiter
export_limiter = Limiter(
    key_func=key_func_export_endpoint,
    default_limits=[export_limit],
    storage_uri=storage_uri,
)

# Auth endpoint limiter - very restrictive
auth_limiter = Limiter(
    key_func=key_func_auth_endpoint,
    default_limits=[auth_limit],
    storage_uri=storage_uri,
)
