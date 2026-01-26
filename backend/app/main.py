from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .routes import words, purchase, leaderboard

settings = get_settings()

app = FastAPI(
    title="The Word Registry API",
    description="A competitive marketplace for exclusive, temporary ownership of English words",
    version="1.0.0"
)

# Include routers
app.include_router(words.router)
app.include_router(purchase.router)
app.include_router(leaderboard.router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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
