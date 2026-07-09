"""
Global application configuration.
...
"""
from functools import lru_cache
from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Runtime ---
    PORT: int = Field(default=8000)
    NODE_ENV: str = Field(default="development")

    # --- CORS ---
    # Comma-separated list, e.g.:
    # CORS_ALLOWED_ORIGINS=https://medicare-frontend.vercel.app,https://app.medicare.com
    CORS_ALLOWED_ORIGINS: str = Field(default="http://localhost:3000")
    # Optional regex for preview deployments, e.g. Vercel branch previews
    CORS_ALLOWED_ORIGIN_REGEX: str | None = Field(default=None)

    # --- Database ---
    DATABASE_URL: str

    # --- Auth / JWT ---
    JWT_SECRET: str
    JWT_ACCESS_EXPIRATION_MINUTES: int = Field(default=30)
    JWT_ALGORITHM: str = Field(default="HS256")

    # --- Field-level encryption at rest ---
    DATA_ENCRYPTION_KEY: str

    # --- Twilio (telehealth) ---
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str

    # --- Stripe (billing) ---
    STRIPE_SECRET_KEY: str

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret_strength(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters long for adequate entropy."
            )
        return value

    @property
    def is_production(self) -> bool:
        return self.NODE_ENV.lower() == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor. FastAPI dependencies should call this via
    `Depends(get_settings)` so settings are constructed once per process
    and can still be overridden in tests via dependency_overrides.
    """
    return Settings()