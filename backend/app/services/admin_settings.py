from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.settings import AppSetting
from app.schemas.admin import SmtpSettingsResponse, SmtpSettingsUpdate
from app.services.auth import EmailDeliveryConfig, get_default_email_delivery_config

SMTP_SETTINGS_KEY = "smtp"


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
        timeout_seconds=int(data.get("timeout_seconds") or 15),
        from_email=data.get("from_email") or settings.SMTP_FROM,
        from_name=data.get("from_name") or settings.SMTP_FROM_NAME,
        frontend_base_url=(data.get("frontend_base_url") or settings.FRONTEND_BASE_URL).rstrip("/"),
        email_verification_ttl_seconds=int(data.get("email_verification_ttl_seconds") or 86400),
        password_reset_ttl_seconds=int(data.get("password_reset_ttl_seconds") or 3600),
    )


async def save_smtp_settings(db: AsyncSession, body: SmtpSettingsUpdate) -> SmtpSettingsResponse:
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
    settings.FRONTEND_BASE_URL = (data.get("frontend_base_url") or settings.FRONTEND_BASE_URL).rstrip("/")
    settings.EMAIL_VERIFICATION_TTL_SECONDS = int(
        data.get("email_verification_ttl_seconds") or settings.EMAIL_VERIFICATION_TTL_SECONDS
    )
    settings.PASSWORD_RESET_TTL_SECONDS = int(
        data.get("password_reset_ttl_seconds") or settings.PASSWORD_RESET_TTL_SECONDS
    )
