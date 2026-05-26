from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.settings import AppSetting
from app.schemas.admin import (
    ApiSettingsResponse,
    ApiSettingsUpdate,
    SmtpSettingsResponse,
    SmtpSettingsUpdate,
)
from app.services.auth import EmailDeliveryConfig, get_default_email_delivery_config

SMTP_SETTINGS_KEY = "smtp"
API_SETTINGS_KEY = "external_api"


def _clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _base_smtp_data() -> dict[str, Any]:
    return {
        "enabled": settings.SMTP_ENABLED,
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "username": settings.SMTP_USERNAME,
        "password": settings.SMTP_PASSWORD,
        "use_ssl": settings.SMTP_USE_SSL,
        "use_tls": settings.SMTP_USE_TLS,
        "force_ipv4": settings.SMTP_FORCE_IPV4,
        "timeout_seconds": settings.SMTP_TIMEOUT_SECONDS,
        "from_email": settings.SMTP_FROM,
        "from_name": settings.SMTP_FROM_NAME,
        "frontend_base_url": settings.FRONTEND_BASE_URL.rstrip("/"),
        "email_verification_ttl_seconds": settings.EMAIL_VERIFICATION_TTL_SECONDS,
        "password_reset_ttl_seconds": settings.PASSWORD_RESET_TTL_SECONDS,
    }


def _base_api_data() -> dict[str, Any]:
    return {
        "steam_api_key": settings.STEAM_API_KEY,
        "faceit_api_key": settings.FACEIT_API_KEY,
        "github_oauth_client_id": settings.GITHUB_OAUTH_CLIENT_ID,
        "github_oauth_client_secret": settings.GITHUB_OAUTH_CLIENT_SECRET,
        "gitlab_oauth_client_id": settings.GITLAB_OAUTH_CLIENT_ID,
        "gitlab_oauth_client_secret": settings.GITLAB_OAUTH_CLIENT_SECRET,
        "gitea_oauth_client_id": settings.GITEA_OAUTH_CLIENT_ID,
        "gitea_oauth_client_secret": settings.GITEA_OAUTH_CLIENT_SECRET,
        "self_hosted_git_oauth_enabled": settings.SELF_HOSTED_GIT_OAUTH_ENABLED,
        "steam_inventory_app_id": settings.STEAM_INVENTORY_APP_ID,
        "steam_inventory_context_id": settings.STEAM_INVENTORY_CONTEXT_ID,
    }


def _secret_hint(value: Optional[str]) -> Optional[str]:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    if len(cleaned) <= 4:
        return "****"
    return f"****{cleaned[-4:]}"


async def _get_setting(db: AsyncSession, key: str) -> Optional[AppSetting]:
    return await db.get(AppSetting, key)


async def get_smtp_data(db: AsyncSession) -> dict[str, Any]:
    data = _base_smtp_data()
    setting = await _get_setting(db, SMTP_SETTINGS_KEY)
    if setting and isinstance(setting.value, dict):
        data.update(setting.value)
    return data


async def get_smtp_response(db: AsyncSession) -> SmtpSettingsResponse:
    data = await get_smtp_data(db)
    return SmtpSettingsResponse(
        enabled=bool(data.get("enabled")),
        host=_clean_text(data.get("host")),
        port=int(data.get("port") or 587),
        username=_clean_text(data.get("username")),
        password_set=bool(_clean_text(data.get("password"))),
        use_ssl=bool(data.get("use_ssl")),
        use_tls=bool(data.get("use_tls")),
        force_ipv4=bool(data.get("force_ipv4")),
        timeout_seconds=int(data.get("timeout_seconds") or 15),
        from_email=data.get("from_email") or settings.SMTP_FROM,
        from_name=data.get("from_name") or settings.SMTP_FROM_NAME,
        frontend_base_url=(
            data.get("frontend_base_url") or settings.FRONTEND_BASE_URL
        ).rstrip("/"),
        email_verification_ttl_seconds=int(
            data.get("email_verification_ttl_seconds") or 86400
        ),
        password_reset_ttl_seconds=int(data.get("password_reset_ttl_seconds") or 3600),
    )


async def get_public_frontend_base_url(db: AsyncSession) -> str:
    data = await get_smtp_data(db)
    return (data.get("frontend_base_url") or settings.FRONTEND_BASE_URL).rstrip("/")


async def get_api_settings_data(db: AsyncSession) -> dict[str, Any]:
    data = _base_api_data()
    setting = await _get_setting(db, API_SETTINGS_KEY)
    if setting and isinstance(setting.value, dict):
        data.update(setting.value)
    return data


async def get_api_settings_response(db: AsyncSession) -> ApiSettingsResponse:
    data = await get_api_settings_data(db)
    steam_api_key = _clean_text(data.get("steam_api_key"))
    faceit_api_key = _clean_text(data.get("faceit_api_key"))
    github_secret = _clean_text(data.get("github_oauth_client_secret"))
    gitlab_secret = _clean_text(data.get("gitlab_oauth_client_secret"))
    gitea_secret = _clean_text(data.get("gitea_oauth_client_secret"))
    return ApiSettingsResponse(
        steam_api_key_set=bool(steam_api_key),
        steam_api_key_hint=_secret_hint(steam_api_key),
        faceit_api_key_set=bool(faceit_api_key),
        faceit_api_key_hint=_secret_hint(faceit_api_key),
        github_oauth_client_id=_clean_text(data.get("github_oauth_client_id")),
        github_oauth_client_secret_set=bool(github_secret),
        github_oauth_client_secret_hint=_secret_hint(github_secret),
        gitlab_oauth_client_id=_clean_text(data.get("gitlab_oauth_client_id")),
        gitlab_oauth_client_secret_set=bool(gitlab_secret),
        gitlab_oauth_client_secret_hint=_secret_hint(gitlab_secret),
        gitea_oauth_client_id=_clean_text(data.get("gitea_oauth_client_id")),
        gitea_oauth_client_secret_set=bool(gitea_secret),
        gitea_oauth_client_secret_hint=_secret_hint(gitea_secret),
        self_hosted_git_oauth_enabled=bool(data.get("self_hosted_git_oauth_enabled")),
        steam_inventory_app_id=int(data.get("steam_inventory_app_id") or 730),
        steam_inventory_context_id=str(data.get("steam_inventory_context_id") or "2"),
        steam_inventory_price_source=(
            "Steam Web API can expose inventory only with publisher Economy permissions; "
            "regular Web API responses do not include market prices."
        ),
    )


async def save_api_settings(
    db: AsyncSession, body: ApiSettingsUpdate
) -> ApiSettingsResponse:
    current = await get_api_settings_data(db)
    payload = body.model_dump(mode="json")

    if body.steam_api_key is None:
        payload["steam_api_key"] = current.get("steam_api_key")
    if body.faceit_api_key is None:
        payload["faceit_api_key"] = current.get("faceit_api_key")
    if body.self_hosted_git_oauth_enabled is None:
        payload["self_hosted_git_oauth_enabled"] = current.get(
            "self_hosted_git_oauth_enabled"
        )
    for key in (
        "github_oauth_client_id",
        "github_oauth_client_secret",
        "gitlab_oauth_client_id",
        "gitlab_oauth_client_secret",
        "gitea_oauth_client_id",
        "gitea_oauth_client_secret",
    ):
        if payload.get(key) is None:
            payload[key] = current.get(key)

    payload["steam_api_key"] = _clean_text(payload.get("steam_api_key"))
    payload["faceit_api_key"] = _clean_text(payload.get("faceit_api_key"))
    payload["self_hosted_git_oauth_enabled"] = bool(
        payload.get("self_hosted_git_oauth_enabled")
    )
    for key in (
        "github_oauth_client_id",
        "github_oauth_client_secret",
        "gitlab_oauth_client_id",
        "gitlab_oauth_client_secret",
        "gitea_oauth_client_id",
        "gitea_oauth_client_secret",
    ):
        payload[key] = _clean_text(payload.get(key))
    payload["steam_inventory_context_id"] = str(
        payload.get("steam_inventory_context_id") or "2"
    ).strip()

    setting = await _get_setting(db, API_SETTINGS_KEY)
    if not setting:
        setting = AppSetting(key=API_SETTINGS_KEY, value=payload)
        db.add(setting)
    else:
        setting.value = payload
        setting.updated_at = datetime.utcnow()
        db.add(setting)

    await db.commit()
    return await get_api_settings_response(db)


async def save_smtp_settings(
    db: AsyncSession, body: SmtpSettingsUpdate
) -> SmtpSettingsResponse:
    current = await get_smtp_data(db)
    payload = body.model_dump(mode="json")

    if body.password is None:
        payload["password"] = current.get("password")

    payload["host"] = _clean_text(payload.get("host"))
    payload["username"] = _clean_text(payload.get("username"))
    payload["password"] = _clean_text(payload.get("password"))
    payload["frontend_base_url"] = payload["frontend_base_url"].rstrip("/")

    setting = await _get_setting(db, SMTP_SETTINGS_KEY)
    if not setting:
        setting = AppSetting(key=SMTP_SETTINGS_KEY, value=payload)
        db.add(setting)
    else:
        setting.value = payload
        setting.updated_at = datetime.utcnow()
        db.add(setting)

    await db.commit()
    return await get_smtp_response(db)


async def get_smtp_delivery_config(db: AsyncSession) -> EmailDeliveryConfig:
    data = await get_smtp_data(db)
    fallback = get_default_email_delivery_config()
    return EmailDeliveryConfig(
        enabled=bool(data.get("enabled")),
        host=_clean_text(data.get("host")),
        port=int(data.get("port") or fallback.port),
        username=_clean_text(data.get("username")),
        password=_clean_text(data.get("password")),
        use_ssl=bool(data.get("use_ssl")),
        use_tls=bool(data.get("use_tls")),
        force_ipv4=bool(data.get("force_ipv4")),
        timeout_seconds=int(data.get("timeout_seconds") or fallback.timeout_seconds),
        from_email=data.get("from_email") or fallback.from_email,
        from_name=data.get("from_name") or fallback.from_name,
    )


async def apply_public_auth_settings(db: AsyncSession) -> None:
    data = await get_smtp_data(db)
    settings.FRONTEND_BASE_URL = (
        data.get("frontend_base_url") or settings.FRONTEND_BASE_URL
    ).rstrip("/")
    settings.EMAIL_VERIFICATION_TTL_SECONDS = int(
        data.get("email_verification_ttl_seconds")
        or settings.EMAIL_VERIFICATION_TTL_SECONDS
    )
    settings.PASSWORD_RESET_TTL_SECONDS = int(
        data.get("password_reset_ttl_seconds") or settings.PASSWORD_RESET_TTL_SECONDS
    )
