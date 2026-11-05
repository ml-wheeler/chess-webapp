import os


class Settings:
    app_env = os.getenv("APP_ENV", "development")
    database_url = os.getenv("DATABASE_URL", "sqlite:///./chess.db")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    frontend_origins = [
        origin.strip()
        for origin in os.getenv(
            "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]
    session_cookie_secure = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    session_ttl_hours = int(os.getenv("SESSION_TTL_HOURS", "336"))
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "accounts@localhost")
    smtp_starttls = os.getenv("SMTP_STARTTLS", "true").lower() == "true"


settings = Settings()
