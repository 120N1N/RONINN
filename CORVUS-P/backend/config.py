import os
from dotenv import load_dotenv
load_dotenv()
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Corvus"
    APP_ENV: str = "development"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@db:5432/corvus")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    API_BASE_URL: str = "http://localhost:8000/api"
    
    # LLM Integrations
    RIVER_API_KEY: str = os.getenv("RIVER_API_KEY", "")
    RIVER_MODEL: str = os.getenv("RIVER_MODEL", "Qwen/Qwen3.5-9B")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    
    # Scan Limits
    MAX_CONCURRENT_SCAN: int = 3
    SCAN_TIMEOUT: int = 300
    QUEUE_LIMIT: int = 10
    
    # Target Scope Control
    MAX_URL: int = 500
    MAX_DEPTH: int = 3
    EXCLUDE_PATHS: List[str] = ["/logout", "/admin"]
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day
    TERMS_OF_USE_ENFORCED: bool = True # Mewajibkan user menyetujui ToS sebelum scan
    
    # Rate Limiting
    RATE_LIMIT_PER_USER_DAY: int = 5
    COOLDOWN_BETWEEN_SCANS_SEC: int = 60
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "https://corvusnoct.my.id",
        "http://corvusnoct.my.id"
    ] if os.getenv("APP_ENV", "development") == "production" else [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1",
        "https://corvusnoct.my.id",
        "http://corvusnoct.my.id"
    ]

    # New Enhancement Settings
    SCAN_CACHE_TTL: int = 3600
    ENABLE_CUSTOM_VULNS: bool = True
    SAFE_RATE_LIMIT_REQUESTS: int = 5
    
    # DoS Testing Configuration
    DOS_TEST_ENABLED: bool = False
    DOS_MAX_REQUESTS: int = 1000
    DOS_BATCH_SIZES: List[int] = [10, 20, 50, 100, 200, 300, 500, 800, 1000]
    DOS_THREAD_WORKERS: int = 10

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

if not settings.JWT_SECRET or len(settings.JWT_SECRET) < 16 or "supersecret" in settings.JWT_SECRET:
    raise ValueError("FATAL ERROR: JWT_SECRET MUST be set in .env to a strong, unique key! Avoid trivial secrets.")
