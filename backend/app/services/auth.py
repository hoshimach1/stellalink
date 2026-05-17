import asyncio
import hashlib
import logging
import re
import secrets
import smtplib
import socket
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from typing import Optional
from urllib.parse import urlencode
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.user import User, UserSession
from app.redis import get_redis

ALGORITHM = "HS256"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailDeliveryConfig:
    enabled: bool
    host: Optional[str]
    port: int
    username: Optional[str]
    password: Optional[str]
    use_ssl: bool
    use_tls: bool
    force_ipv4: bool
    timeout_seconds: int
    from_email: str
    from_name: str


def get_default_email_delivery_config() -> EmailDeliveryConfig:
    return EmailDeliveryConfig(
        enabled=settings.SMTP_ENABLED,
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        use_ssl=settings.SMTP_USE_SSL,
        use_tls=settings.SMTP_USE_TLS,
        force_ipv4=settings.SMTP_FORCE_IPV4,
        timeout_seconds=settings.SMTP_TIMEOUT_SECONDS,
        from_email=settings.SMTP_FROM,
        from_name=settings.SMTP_FROM_NAME,
    )


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def validate_password(password: str) -> Optional[str]:
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if not re.search(r"[A-Za-z]", password):
        return "Password must include at least one letter"
    if not re.search(r"\d", password):
        return "Password must include at least one digit"
    return None


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


async def create_session(
    db: AsyncSession,
    user: User,
    user_agent: Optional[str],
    ip_address: Optional[str],
) -> tuple[str, str]:
    """Returns (access_token, refresh_token)."""
    refresh_token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    session = UserSession(
        user_id=user.id,
        refresh_token=refresh_token,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()

    access_token = create_access_token(str(user.id))
    return access_token, refresh_token


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_session_by_refresh_token(
    db: AsyncSession, token: str
) -> Optional[UserSession]:
    result = await db.execute(
        select(UserSession)
        .options(selectinload(UserSession.user))
        .where(
            UserSession.refresh_token == token,
            UserSession.expires_at > datetime.now(timezone.utc),
            UserSession.user.has(User.deleted_at.is_(None)),
        )
    )
    return result.scalar_one_or_none()


async def revoke_refresh_session(db: AsyncSession, refresh_token: str) -> bool:
    session = await get_session_by_refresh_token(db, refresh_token)
    if not session:
        return False
    await db.delete(session)
    await db.commit()
    return True


async def revoke_user_sessions(
    db: AsyncSession,
    user_id: UUID,
    exclude_refresh_token: Optional[str] = None,
) -> None:
    stmt = delete(UserSession).where(UserSession.user_id == user_id)
    if exclude_refresh_token:
        stmt = stmt.where(UserSession.refresh_token != exclude_refresh_token)

    await db.execute(stmt)
    await db.commit()


def _auth_key(namespace: str, token: str) -> str:
    return f"auth:{namespace}:{token}"


def _rate_key(kind: str, identifier: str) -> str:
    return f"auth:login:{kind}:{identifier}"


def _normalize_base_url(url: str) -> str:
    return url.rstrip("/")


def _build_frontend_url(path: str, query: dict[str, str]) -> str:
    normalized_path = "/" + path.lstrip("/")
    return f"{_normalize_base_url(settings.FRONTEND_BASE_URL)}{normalized_path}?{urlencode(query)}"


def make_login_attempt_identifier(email: str, ip_address: Optional[str]) -> str:
    normalized_email = email.strip().lower()
    normalized_ip = (ip_address or "unknown").strip().lower()
    digest = hashlib.sha256(
        f"{normalized_email}|{normalized_ip}".encode("utf-8")
    ).hexdigest()
    return digest


async def _redis_get(key: str) -> Optional[str]:
    try:
        redis = await get_redis()
        return await redis.get(key)
    except Exception:  # noqa: BLE001
        logger.exception("Redis get failed for key %s", key)
        return None


async def _redis_setex(key: str, ttl_seconds: int, value: str) -> bool:
    try:
        redis = await get_redis()
        await redis.setex(key, ttl_seconds, value)
        return True
    except Exception:  # noqa: BLE001
        logger.exception("Redis setex failed for key %s", key)
        return False


async def _redis_delete(*keys: str) -> None:
    if not keys:
        return
    try:
        redis = await get_redis()
        await redis.delete(*keys)
    except Exception:  # noqa: BLE001
        logger.exception("Redis delete failed for keys %s", keys)


async def _redis_ttl(key: str) -> int:
    try:
        redis = await get_redis()
        ttl = await redis.ttl(key)
        return max(int(ttl), 0)
    except Exception:  # noqa: BLE001
        logger.exception("Redis ttl failed for key %s", key)
        return 0


async def create_email_verification_token(user_id: UUID, email: str) -> str:
    token = secrets.token_urlsafe(48)
    payload = f"{user_id}|{email.strip().lower()}"
    await _redis_setex(
        _auth_key("verify", token), settings.EMAIL_VERIFICATION_TTL_SECONDS, payload
    )
    return token


async def consume_email_verification_token(token: str) -> Optional[dict[str, str]]:
    key = _auth_key("verify", token)
    raw = await _redis_get(key)
    if not raw or "|" not in raw:
        return None
    user_id, email = raw.split("|", 1)
    await _redis_delete(key)
    return {"user_id": user_id, "email": email}


async def create_password_reset_token(user_id: UUID, email: str) -> str:
    token = secrets.token_urlsafe(48)
    payload = f"{user_id}|{email.strip().lower()}"
    await _redis_setex(
        _auth_key("reset", token), settings.PASSWORD_RESET_TTL_SECONDS, payload
    )
    return token


async def consume_password_reset_token(token: str) -> Optional[dict[str, str]]:
    key = _auth_key("reset", token)
    raw = await _redis_get(key)
    if not raw or "|" not in raw:
        return None
    user_id, email = raw.split("|", 1)
    await _redis_delete(key)
    return {"user_id": user_id, "email": email}


async def get_login_lock_ttl_seconds(identifier: str) -> int:
    return await _redis_ttl(_rate_key("lock", identifier))


async def register_failed_login_attempt(identifier: str) -> int:
    fail_key = _rate_key("fail", identifier)
    lock_key = _rate_key("lock", identifier)

    try:
        redis = await get_redis()
        attempts = await redis.incr(fail_key)
        if attempts == 1:
            await redis.expire(fail_key, settings.LOGIN_ATTEMPT_WINDOW_SECONDS)

        if attempts >= settings.LOGIN_MAX_ATTEMPTS:
            await redis.setex(lock_key, settings.LOGIN_LOCKOUT_SECONDS, str(attempts))
            await redis.delete(fail_key)
            return settings.LOGIN_MAX_ATTEMPTS

        return int(attempts)
    except Exception:  # noqa: BLE001
        logger.exception("Unable to register failed login attempt")
        return 0


async def clear_failed_login_attempts(identifier: str) -> None:
    await _redis_delete(_rate_key("fail", identifier), _rate_key("lock", identifier))


def build_email_verification_url(token: str) -> str:
    return _build_frontend_url("/auth/verify-email", {"token": token})


def build_password_reset_url(token: str) -> str:
    return _build_frontend_url("/auth/reset-password", {"token": token})


def _build_action_email_html(
    title: str,
    intro: str,
    action_label: str,
    action_url: str,
    expires_note: str,
    footer: str,
) -> str:
    safe_title = escape(title)
    safe_intro = escape(intro)
    safe_label = escape(action_label)
    safe_url = escape(action_url, quote=True)
    safe_expires = escape(expires_note)
    safe_footer = escape(footer)
    safe_brand = escape(settings.SMTP_FROM_NAME)

    return f"""<!doctype html>
<html lang="en">
  <body style="margin:0;background:#f4f6fb;font-family:Arial,sans-serif;color:#1a2438;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f6fb;padding:32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#ffffff;border:1px solid #e2e7f2;border-radius:18px;padding:32px;">
            <tr>
              <td style="font-size:14px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:#4f67ab;padding-bottom:18px;">{safe_brand}</td>
            </tr>
            <tr>
              <td style="font-size:26px;line-height:1.25;font-weight:700;padding-bottom:12px;">{safe_title}</td>
            </tr>
            <tr>
              <td style="font-size:16px;line-height:1.6;color:#52617f;padding-bottom:24px;">{safe_intro}</td>
            </tr>
            <tr>
              <td style="padding-bottom:24px;">
                <a href="{safe_url}" style="display:inline-block;background:#1d2433;color:#ffffff;text-decoration:none;font-size:16px;font-weight:700;border-radius:12px;padding:14px 20px;">{safe_label}</a>
              </td>
            </tr>
            <tr>
              <td style="font-size:14px;line-height:1.6;color:#6a7690;padding-bottom:16px;">{safe_expires}</td>
            </tr>
            <tr>
              <td style="font-size:13px;line-height:1.6;color:#8190ab;word-break:break-all;">If the button does not work, copy this link:<br><a href="{safe_url}" style="color:#2e4f98;">{safe_url}</a></td>
            </tr>
            <tr>
              <td style="font-size:13px;line-height:1.6;color:#8190ab;padding-top:24px;">{safe_footer}</td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def _resolve_smtp_host(delivery: EmailDeliveryConfig) -> str:
    if not delivery.force_ipv4 or not delivery.host:
        return delivery.host or ""

    addresses = socket.getaddrinfo(
        delivery.host, delivery.port, family=socket.AF_INET, type=socket.SOCK_STREAM
    )
    if not addresses:
        raise OSError(f"No IPv4 address found for SMTP host {delivery.host}")

    return addresses[0][4][0]


def _open_smtp_connection(
    delivery: EmailDeliveryConfig,
) -> AbstractContextManager[smtplib.SMTP]:
    host = _resolve_smtp_host(delivery)
    if delivery.use_ssl:
        return smtplib.SMTP_SSL(
            host,
            delivery.port,
            timeout=delivery.timeout_seconds,
        )

    return smtplib.SMTP(
        host,
        delivery.port,
        timeout=delivery.timeout_seconds,
    )


def _send_email_sync(
    to_email: str,
    subject: str,
    text: str,
    html: Optional[str] = None,
    delivery_config: Optional[EmailDeliveryConfig] = None,
) -> None:
    delivery = delivery_config or get_default_email_delivery_config()
    msg = EmailMessage()
    msg["From"] = formataddr((delivery.from_name, delivery.from_email))
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")

    if not delivery.enabled or not delivery.host:
        logger.info(
            "SMTP is not configured. Email to %s: %s\n%s", to_email, subject, text
        )
        return

    with _open_smtp_connection(delivery) as server:
        if delivery.use_tls and not delivery.use_ssl:
            server.starttls()
        if delivery.username and delivery.password:
            server.login(delivery.username, delivery.password)
        server.send_message(msg)


async def send_auth_email(
    to_email: str,
    subject: str,
    text: str,
    html: Optional[str] = None,
    delivery_config: Optional[EmailDeliveryConfig] = None,
    raise_errors: bool = False,
) -> None:
    try:
        await asyncio.to_thread(
            _send_email_sync, to_email, subject, text, html, delivery_config
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send auth email to %s", to_email)
        if raise_errors:
            raise


async def send_email_verification_email(
    to_email: str,
    token: str,
    delivery_config: Optional[EmailDeliveryConfig] = None,
) -> None:
    verification_url = build_email_verification_url(token)
    subject = "Verify your Stellalink email"
    expires_note = (
        f"This link expires in {settings.EMAIL_VERIFICATION_TTL_SECONDS // 3600} hours."
    )
    text = (
        "Please verify your email for Stellalink.\n\n"
        f"Open this link: {verification_url}\n\n"
        f"{expires_note}\n"
        "If you did not create this account, you can ignore this email."
    )
    html = _build_action_email_html(
        title="Verify your email",
        intro="Please confirm this email address to finish setting up your Stellalink account.",
        action_label="Verify email",
        action_url=verification_url,
        expires_note=expires_note,
        footer="If you did not create a Stellalink account, you can safely ignore this email.",
    )
    await send_auth_email(to_email, subject, text, html, delivery_config)


async def send_password_reset_email(
    to_email: str,
    token: str,
    delivery_config: Optional[EmailDeliveryConfig] = None,
) -> None:
    reset_url = build_password_reset_url(token)
    subject = "Reset your Stellalink password"
    expires_note = (
        f"This link expires in {settings.PASSWORD_RESET_TTL_SECONDS // 60} minutes."
    )
    text = (
        "We received a password reset request for your Stellalink account.\n\n"
        f"Open this link: {reset_url}\n\n"
        f"{expires_note}\n"
        "If you did not request this, you can ignore this email."
    )
    html = _build_action_email_html(
        title="Reset your password",
        intro="We received a password reset request for your Stellalink account.",
        action_label="Reset password",
        action_url=reset_url,
        expires_note=expires_note,
        footer="If you did not request this, no action is needed.",
    )
    await send_auth_email(to_email, subject, text, html, delivery_config)
