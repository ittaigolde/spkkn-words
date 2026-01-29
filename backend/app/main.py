from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

from .config import get_settings
from .routes import words, purchase, leaderboard, payment, admin, product_feed
from .cache import init_cache
from .ratelimit import limiter, rate_limit_exceeded_handler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    try:
        # Startup: Initialize cache
        await init_cache()
        print("Cache initialized")
        print("Server is ready")
        yield
    except Exception as e:
        print(f"Error during startup: {e}")
        raise
    finally:
        # Shutdown: cleanup if needed
        print("Shutting down")


app = FastAPI(
    title="The Word Registry API",
    description="A competitive marketplace for exclusive, temporary ownership of English words",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting
if settings.rate_limit_enabled:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Include routers
app.include_router(words.router)
app.include_router(purchase.router)
app.include_router(leaderboard.router)
app.include_router(payment.router)
app.include_router(admin.router)
app.include_router(product_feed.router)

# CORS middleware
# Parse comma-separated origins from settings
cors_origins = settings.cors_origins.split(",") if settings.cors_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "The Word Registry API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "environment": settings.app_env
    }
