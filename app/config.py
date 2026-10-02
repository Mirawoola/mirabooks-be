"""
Mirabooks Backend Configuration.

Uses pydantic-settings to load and validate environment variables.
This is the single source of truth for all configuration — no magic
strings scattered through the codebase.

WHY pydantic-settings?
- Validates types at startup (catches missing keys early)
- Provides autocomplete in IDEs
- Documents every config value in one place
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str
    database_url: str

    # Google OAuth
    google_client_id: str
    google_client_secret: str

    # Paystack
    paystack_secret_key: str
    paystack_public_key: str

    # Mailgun
    mailgun_api_key: str
    mailgun_domain: str
    mailgun_sender_email: str = "orders@mirabooks.com"

    # App
    app_secret_key: str
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


settings = Settings()
