"""Application configuration."""

from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Application settings."""
    
    BACKEND_URL: str
    OPENROUTER_API_KEY: str
    # Google OAuth settings
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    GOOGLE_CALENDAR_SCOPES: list[str] = [
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid"
    ]
    GOOGLE_AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    GOOGLE_LOGIN_URI: str = "http://localhost:8000/auth/google/login"
    
    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    class Config:
        env_file = ".env"

settings = Settings()