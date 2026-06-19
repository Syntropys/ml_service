"""
Application configuration using pydantic-settings.
All environment variables are loaded from .env file or system environment.
"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the Paddy ML Bridge API."""

    # --- Project ---
    PROJECT_NAME: str = "Paddy ML Bridge API"
    VERSION: str = "3.0.0"
    DEBUG: bool = False

    # --- Supabase ---
    SUPABASE_URL: str = "https://mawewomqcdnsqnxmkjlq.supabase.co"
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = "super-secret-jwt-token"

    # --- Embedded Models (v3 — no external ML services) ---
    MODEL_DIR: str = str(Path(__file__).resolve().parent.parent / "models")

    # --- MLflow Tracking (optional, for experiment logging only) ---
    MLFLOW_TRACKING_URI: str = "sqlite:///mlruns.db"

    # --- CORS ---
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://agrolytics.my.id",
    ]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
