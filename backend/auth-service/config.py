import os
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

from shared.config import Settings as SharedSettings


class AuthServiceSettings(BaseSettings):
    """Auth service specific settings."""
    
    # Service configuration
    PORT: int = Field(default=8001, description="Port the auth service runs on")
    HOST: str = Field(default="0.0.0.0", description="Host to bind the service to")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    
    # JWT configuration
    JWT_SECRET: SecretStr = Field(
        default_factory=lambda: SecretStr(os.getenv("JWT_SECRET", "your-secret-key-change-in-production")),
        description="Secret key for JWT token signing"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="Algorithm for JWT token signing")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )
    
    # Password hashing
    BCRYPT_ROUNDS: int = Field(default=12, description="Number of bcrypt rounds for password hashing")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="Maximum number of requests per minute per IP"
    )
    
    # Security
    REQUIRE_EMAIL_VERIFICATION: bool = Field(
        default=False,
        description="Require email verification for new users"
    )
    ALLOW_REGISTRATION: bool = Field(
        default=True,
        description="Allow new user registration"
    )
    
    # Token blacklist
    TOKEN_BLACKLIST_ENABLED: bool = Field(
        default=True,
        description="Enable token blacklisting for logout"
    )
    TOKEN_BLACKLIST_TTL_HOURS: int = Field(
        default=24,
        description="Time to keep tokens in blacklist (hours)"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_settings()
    
    def _validate_settings(self) -> None:
        """Validate settings and raise errors for invalid configurations."""
        # Validate JWT secret
        if self.JWT_SECRET.get_secret_value() == "your-secret-key-change-in-production":
            import warnings
            warnings.warn(
                "Using default JWT secret. Change JWT_SECRET environment variable in production.",
                UserWarning
            )
        
        # Validate token expiration times
        if self.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
        
        if self.REFRESH_TOKEN_EXPIRE_DAYS <= 0:
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be positive")
        
        # Validate bcrypt rounds
        if not 4 <= self.BCRYPT_ROUNDS <= 31:
            raise ValueError("BCRYPT_ROUNDS must be between 4 and 31")
        
        # Validate rate limit
        if self.RATE_LIMIT_PER_MINUTE <= 0:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be positive")
        
        # Validate port
        if not 1 <= self.PORT <= 65535:
            raise ValueError("PORT must be between 1 and 65535")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.LOG_LEVEL.upper() not in valid_log_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_log_levels}")


# Global settings instance
settings = AuthServiceSettings()

# Import shared settings for convenience
shared_settings = SharedSettings()
