import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, model_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "JewelAI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    MOCK_INSTAGRAM_API: bool = False
    MOCK_AI_PROVIDER: bool = False
    
    # Security
    SECRET_KEY: str = "jewelai-super-secret-jwt-key-2026-min-32-chars-long"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Encryption key for Meta tokens (Fernet 32 url-safe base64 key)
    ENCRYPTION_KEY: str = "tV9F0XJ5E8Yw7R2L6c3K1Z9p4U8q7W2e5A0b3C6d9E8="
    
    # Registration & Rate Limiting
    REGISTRATION_INVITE_CODE: str = "JEWELAI_INVITE_2026"
    ENABLE_OPEN_REGISTRATION: bool = False
    ENABLE_DIRECT_TOKEN_CONNECT: bool = False
    AUTH_RATE_LIMIT_PER_MINUTE: int = 10
    
    # Database & Cache
    DATABASE_URL: str = "sqlite:///./jewelai.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Meta / Instagram Configuration
    META_GRAPH_URL: str = "https://graph.instagram.com"
    META_API_VERSION: str = "v22.0"
    INSTAGRAM_APP_ID: str = ""
    INSTAGRAM_APP_SECRET: str = ""
    INSTAGRAM_WEBHOOK_VERIFY_TOKEN: str = "jewelai_verify_token_secure_2026"
    INSTAGRAM_REDIRECT_URI: str = "http://localhost:3000/auth/instagram/callback"
    MESSAGING_WINDOW_HOURS: int = 24
    COMMENT_AUTO_DM_DAILY_CAP: int = 50
    
    # AI Engine Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_TEXT_MODEL: str = "gemini-3.8-flash"
    GEMINI_VISION_MODEL: str = "gemini-3.8-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    AI_CONFIDENCE_THRESHOLD: float = 0.70
    AI_MAX_CONTEXT_MESSAGES: int = 10
    
    # Business defaults
    DEFAULT_BUSINESS_NAME: str = ""
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_LANGUAGES: List[str] = ["en", "hi", "gu"]
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"
        extra = "ignore"

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if self.MOCK_INSTAGRAM_API or self.MOCK_AI_PROVIDER:
                raise ValueError("Production must not enable mock integrations.")
            if self.DEBUG:
                raise ValueError("Production DEBUG must be false.")
            insecure_keys = [
                "jewelai-super-secret-jwt-key-2026-min-32-chars-long",
                "change-this-to-a-super-secret-random-jwt-key-2026",
                "insecure-dev-secret-key-replace-in-production-min32chars"
            ]
            if self.SECRET_KEY in insecure_keys or len(self.SECRET_KEY) < 32:
                raise ValueError("CRITICAL: Production SECRET_KEY must be set to a secure, random string with at least 32 characters in production.")

            insecure_enc_keys = [
                "tV9F0XJ5E8Yw7R2L6c3K1Z9p4U8q7W2e5A0b3C6d9E8=",
                "your_fernet_32_urlsafe_base64_encryption_key_here"
            ]
            if not self.ENCRYPTION_KEY or self.ENCRYPTION_KEY in insecure_enc_keys:
                raise ValueError("CRITICAL: Production ENCRYPTION_KEY must be set to a custom, non-default 32 url-safe base64 key in production.")
            from cryptography.fernet import Fernet
            Fernet(self.ENCRYPTION_KEY.encode())
            if not self.ENABLE_OPEN_REGISTRATION and (
                len(self.REGISTRATION_INVITE_CODE) < 16 or self.REGISTRATION_INVITE_CODE == "JEWELAI_INVITE_2026"
            ):
                raise ValueError("Set a private REGISTRATION_INVITE_CODE of at least 16 characters for production.")
            if not self.INSTAGRAM_REDIRECT_URI.startswith("https://"):
                raise ValueError("Production INSTAGRAM_REDIRECT_URI must use HTTPS.")
            if not self.INSTAGRAM_WEBHOOK_VERIFY_TOKEN or self.INSTAGRAM_WEBHOOK_VERIFY_TOKEN == "jewelai_verify_token_secure_2026":
                raise ValueError("Set a private INSTAGRAM_WEBHOOK_VERIFY_TOKEN for production.")
            if not self.INSTAGRAM_APP_ID or not self.INSTAGRAM_APP_SECRET or not self.GEMINI_API_KEY:
                raise ValueError("Production Instagram and Gemini credentials must be configured.")
            if not self.DATABASE_URL.startswith("postgresql"):
                raise ValueError("Production requires PostgreSQL.")
        return self


settings = Settings()
