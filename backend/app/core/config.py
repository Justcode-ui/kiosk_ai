"""
KioskAI Configuration Module
Centralized configuration management using Pydantic Settings
"""
from typing import List, Optional, Union, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "KioskAI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = Field(..., min_length=32)
    
    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection URL")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # Groq AI Configuration
    GROQ_API_KEY: str = Field(..., description="Groq API key")
    GROQ_API_ENDPOINT: str = Field(
        default="https://api.groq.com/openai/v1/chat/completions"
    )
    GROQ_MODEL: str = Field(default="llama-3.1-70b-versatile")
    AI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=1.0)
    AI_MAX_TOKENS: int = Field(default=500, ge=1)
    
    # SMTP Email Configuration
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = Field(default="noreply@kioskai.com")
    SMTP_TLS: bool = True
    
    # Notification Settings
    ENABLE_EMAIL_NOTIFICATIONS: bool = True
    ENABLE_SMS_NOTIFICATIONS: bool = True
    ENABLE_WEBSOCKET_NOTIFICATIONS: bool = True
    HIGH_VALUE_LEAD_THRESHOLD: float = Field(default=50000.0)  # in Naira
    
    # Webhook Configuration (for Telegram Bot)
    WEBHOOK_BASE_URL: Optional[str] = Field(
        default=None,
        description="Base URL for webhooks (e.g., https://yourdomain.com). Required for Telegram bot to receive messages."
    )
    
    # JWT Authentication
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:3000", "http://localhost:8000"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str], Any]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.strip().startswith("["):
            return [i.strip() for i in v.split(",")]
        return v
    
    # Sentry Monitoring
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0")
    
    # AI Settings
    CONVERSATION_MEMORY_LIMIT: int = Field(default=10, ge=1)
    AUTO_REPLY_ENABLED: bool = True
    
    # Follow-up Settings
    FOLLOW_UP_DELAY_HOURS: int = Field(default=24, ge=1)
    AUTO_FOLLOW_UP_ENABLED: bool = True
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=1)
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, ge=1)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
