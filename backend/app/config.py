from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    ADMIN_EMAILS: str | None = None

    SMTP_ENABLED: bool = True
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_SSL: bool = False
    SMTP_USE_TLS: bool = True
    SMTP_FORCE_IPV4: bool = False
    SMTP_TIMEOUT_SECONDS: int = 15
    SMTP_FROM: str = "no-reply@stellalink.app"
    SMTP_FROM_NAME: str = "Stellalink"

    AUTH_DEBUG_TOKENS: bool = False

    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_SECONDS: int = 900
    LOGIN_ATTEMPT_WINDOW_SECONDS: int = 900

    EMAIL_VERIFICATION_TTL_SECONDS: int = 86400
    PASSWORD_RESET_TTL_SECONDS: int = 3600

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def admin_email_set(self) -> set[str]:
        if not self.ADMIN_EMAILS:
            return set()
        return {
            email.strip().lower()
            for email in self.ADMIN_EMAILS.split(",")
            if email.strip()
        }


settings = Settings()
