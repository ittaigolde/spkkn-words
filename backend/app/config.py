from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str

    # Redis (optional - uses in-memory cache if not set)
    redis_url: str | None = None

    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""  # Optional for local testing

    # Application
    app_env: str = "development"
    debug: bool = True

    # Rate Limiting
    rate_limit_enabled: bool = True

    # CORS (comma-separated list of allowed origins)
    cors_origins: str = "*"  # Use "*" for dev, "https://yourdomain.com" for production

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
