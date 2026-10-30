import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import model_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH26262 AICTE Approval & Compliance Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sih26262-dev-super-secret-key-32-chars-long-minimum!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sih_workflow.db")

    # Storage
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./document_storage")
    MAX_FILE_SIZE_BYTES: int = int(os.getenv("MAX_FILE_SIZE_BYTES", 10 * 1024 * 1024)) # 10MB

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]


    @model_validator(mode="after")
    def validate_production_configuration(self):
        if self.ENVIRONMENT.lower() == "production":
            if self.SECRET_KEY == "sih26262-dev-super-secret-key-32-chars-long-minimum!" or len(self.SECRET_KEY) < 32:
                raise ValueError("Production requires a unique SECRET_KEY of at least 32 characters.")
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError("Production must use PostgreSQL or another explicitly supported managed database.")
            # Local Compose binds the frontend to loopback HTTP only. Permit those
            # exact loopback origins for the isolated local demo; all non-loopback
            # production origins must use HTTPS.
            loopback_http = {
                "http://localhost:5173", "http://127.0.0.1:5173",
                "http://localhost:3000", "http://127.0.0.1:3000",
            }
            if not self.BACKEND_CORS_ORIGINS or any(
                not origin.startswith("https://") and origin not in loopback_http
                for origin in self.BACKEND_CORS_ORIGINS
            ):
                raise ValueError("Production CORS origins must use HTTPS, except the exact loopback origins used by local Compose.")
        return self

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure storage directory exists
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
