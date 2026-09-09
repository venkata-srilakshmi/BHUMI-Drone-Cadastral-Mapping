import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR.parent / "data"
STORAGE_DIR = DATA_DIR / "storage"
DEMO_DIR = DATA_DIR / "demo"

class Settings(BaseSettings):
    PROJECT_NAME: str = "BHOOMI-AI"
    TAGLINE: str = "From Drone Imagery to Verified Digital Land Maps"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "bhoomi-secret-key-sih2026-cadastral-ai-mord")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/bhoomi.db")
    
    # File Storage
    STORAGE_PATH: Path = STORAGE_DIR
    DEMO_PATH: Path = DEMO_DIR
    MAX_UPLOAD_SIZE_MB: int = 250
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    class Config:
        case_sensitive = True

settings = Settings()

# Ensure directories exist
os.makedirs(settings.STORAGE_PATH, exist_ok=True)
os.makedirs(settings.DEMO_PATH, exist_ok=True)
