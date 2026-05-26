from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class SmtpSettingsResponse(BaseModel):
    enabled: bool
    host: Optional[str]
    port: int
    username: Optional[str]
    password_set: bool
    use_ssl: bool
    use_tls: bool
    force_ipv4: bool
    timeout_seconds: int
    from_email: EmailStr
    from_name: str
    frontend_base_url: str
    email_verification_ttl_seconds: int
    password_reset_ttl_seconds: int


class SmtpSettingsUpdate(BaseModel):
    enabled: bool = True
    host: Optional[str] = None
    port: int = Field(default=587, ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    use_ssl: bool = False
    use_tls: bool = True
    force_ipv4: bool = False
    timeout_seconds: int = Field(default=15, ge=1, le=120)
    from_email: EmailStr
    from_name: str = Field(min_length=1, max_length=100)
    frontend_base_url: str = Field(min_length=1, max_length=500)
    email_verification_ttl_seconds: int = Field(default=86400, ge=300, le=604800)
    password_reset_ttl_seconds: int = Field(default=3600, ge=300, le=86400)

    @field_validator("host", "username", "password", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("frontend_base_url")
    @classmethod
    def normalize_frontend_base_url(cls, value: str) -> str:
        return value.strip().rstrip("/")


class SmtpTestRequest(BaseModel):
    to_email: Optional[EmailStr] = None


class ApiSettingsResponse(BaseModel):
    steam_api_key_set: bool
    steam_api_key_hint: Optional[str] = None
    faceit_api_key_set: bool
    faceit_api_key_hint: Optional[str] = None
    github_oauth_client_id: Optional[str] = None
    github_oauth_client_secret_set: bool = False
    github_oauth_client_secret_hint: Optional[str] = None
    gitlab_oauth_client_id: Optional[str] = None
    gitlab_oauth_client_secret_set: bool = False
    gitlab_oauth_client_secret_hint: Optional[str] = None
    gitea_oauth_client_id: Optional[str] = None
    gitea_oauth_client_secret_set: bool = False
    gitea_oauth_client_secret_hint: Optional[str] = None
    self_hosted_git_oauth_enabled: bool = False
    steam_inventory_app_id: int
    steam_inventory_context_id: str
    steam_inventory_price_source: str


class ApiSettingsUpdate(BaseModel):
    steam_api_key: Optional[str] = None
    faceit_api_key: Optional[str] = None
    github_oauth_client_id: Optional[str] = None
    github_oauth_client_secret: Optional[str] = None
    gitlab_oauth_client_id: Optional[str] = None
    gitlab_oauth_client_secret: Optional[str] = None
    gitea_oauth_client_id: Optional[str] = None
    gitea_oauth_client_secret: Optional[str] = None
    self_hosted_git_oauth_enabled: Optional[bool] = None
    steam_inventory_app_id: int = Field(default=730, ge=1)
    steam_inventory_context_id: str = Field(default="2", min_length=1, max_length=32)

    @field_validator(
        "steam_api_key",
        "faceit_api_key",
        "github_oauth_client_id",
        "github_oauth_client_secret",
        "gitlab_oauth_client_id",
        "gitlab_oauth_client_secret",
        "gitea_oauth_client_id",
        "gitea_oauth_client_secret",
        "steam_inventory_context_id",
        mode="before",
    )
    @classmethod
    def empty_api_string_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class AdminActionResponse(BaseModel):
    detail: str
