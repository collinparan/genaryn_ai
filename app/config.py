"""
Application configuration using Pydantic Settings
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_ENV: str = Field(default="development", description="Application environment")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # Database
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_PORT: int = Field(default=5432, description="Database port")
    DB_USER: str = Field(default="genaryn", description="Database user")
    DB_PASSWORD: str = Field(default="secure_password", description="Database password")
    DB_NAME: str = Field(default="genaryn_db", description="Database name")

    # Redis
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: str = Field(default="redis_password", description="Redis password")

    # LLM Configuration
    DO_LLM_ENDPOINT: str = Field(
        default="https://w3af7ebiihzxumrnhjb2nh2o.agents.do-ai.run/api/v1/chat/completions",
        description="Digital Ocean LLM endpoint",
    )
    LLM_MODEL: str = Field(
        default="gpt-oss-120b", description="LLM model to use"
    )

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key for signing tokens",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="Access token expiration in minutes"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiration in days"
    )

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:80", "http://localhost"],
        description="Allowed CORS origins",
    )

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60, description="Rate limit per minute"
    )
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, description="Rate limit per hour")

    # Security
    BCRYPT_ROUNDS: int = Field(default=12, description="Bcrypt hashing rounds")
    MAX_LOGIN_ATTEMPTS: int = Field(
        default=5, description="Maximum login attempts before lockout"
    )
    LOCKOUT_DURATION_MINUTES: int = Field(
        default=15, description="Account lockout duration in minutes"
    )

    # Session
    SESSION_SECRET_KEY: str = Field(
        default="session-secret-change-in-production",
        description="Session secret key",
    )
    SESSION_EXPIRE_HOURS: int = Field(
        default=24, description="Session expiration in hours"
    )

    # Feature Flags
    ENABLE_WEBSOCKET: bool = Field(default=True, description="Enable WebSocket support")
    ENABLE_SSE: bool = Field(default=True, description="Enable Server-Sent Events")
    ENABLE_DECISION_ANALYSIS: bool = Field(
        default=True, description="Enable decision analysis features"
    )
    ENABLE_INTELLIGENCE_PROCESSING: bool = Field(
        default=True, description="Enable intelligence processing"
    )
    ENABLE_MISSION_PLANNING: bool = Field(
        default=True, description="Enable mission planning features"
    )
    ENABLE_COLLABORATION: bool = Field(
        default=True, description="Enable multi-user collaboration"
    )

    # Military Configuration
    DEFAULT_CLASSIFICATION: str = Field(
        default="UNCLASSIFIED", description="Default classification level"
    )
    ENABLE_CLASSIFICATION_HANDLING: bool = Field(
        default=True, description="Enable classification handling"
    )
    MDMP_MODE: str = Field(
        default="enhanced", description="Military Decision Making Process mode"
    )
    COA_ANALYSIS_DEPTH: str = Field(
        default="comprehensive", description="Course of Action analysis depth"
    )

    # Monitoring
    PROMETHEUS_PORT: int = Field(
        default=9090, description="Prometheus metrics port"
    )
    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics collection")

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def database_url(self) -> str:
        """Construct database URL."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def redis_url(self) -> str:
        """Construct Redis URL."""
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()