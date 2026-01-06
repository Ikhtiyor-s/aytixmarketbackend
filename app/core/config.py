from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/cursor_market"

    # Database pool settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # JWT - Production uchun SECRET_KEY .env dan o'qilishi SHART
    # Default key faqat development uchun
    SECRET_KEY: str = "aytix-marketplace-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 soat
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS - Production domainlari
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3005",
        "http://localhost:3010",
        "http://localhost:8000",
        "https://admin.aytix.uz",
        "https://aytix.uz",
        "https://www.aytix.uz",
        "https://api.aytix.uz"
    ]

    # App
    PROJECT_NAME: str = "AyTiX Marketplace API"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Upload settings
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/webm", "video/quicktime"]

    # Telegram Bot settings
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = "aytixuz_bot"

    # OpenAI settings
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()



