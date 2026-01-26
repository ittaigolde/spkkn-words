"""
Rate limiting configuration using slowapi.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from .rate_config import RateLimits


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    """
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}",
            "retry_after": "Please try again later"
        },
    )


# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[RateLimits.DEFAULT],  # Global default from config
    storage_uri="memory://",  # Use in-memory storage (can change to redis:// later)
)
