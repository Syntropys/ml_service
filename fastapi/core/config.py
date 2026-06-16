"""
Application configuration using pydantic-settings.
All environment variables are loaded from .env file or system environment.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the Paddy ML Bridge API."""

    # --- Project ---
    PROJECT_NAME: str = "Paddy ML Bridge API"
    VERSION: str = "2.0.0"
    DEBUG: bool = False

    # --- Supabase ---
    SUPABASE_URL: str = "https://mawewomqcdnsqnxmkjlq.supabase.co"
    SUPABASE_ANON_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1hd2V3b21xY2Ruc3FueG1ramxxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzk5NjE3NDYsImV4cCI6MjA5NTUzNzc0Nn0.C8-XJL8B6_EyBTKo7UEL9Rmz5-BMvB1Y3GG8RnkND24"
    SUPABASE_SERVICE_ROLE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1hd2V3b21xY2Ruc3FueG1ramxxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTk2MTc0NiwiZXhwIjoyMDk1NTM3NzQ2fQ.n0qKoq62vmuAm5t1_mqv5iUDUkRrplrp331ZSFAQ8GI"
    SUPABASE_JWT_SECRET: str = "super-secret-jwt-token"

    # --- ML Service (Bridge Pattern) ---
    ML_SERVICE_URL: str = "http://ml-service:8000"

    # --- MLflow Tracking ---
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
