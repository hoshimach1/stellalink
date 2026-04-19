import asyncio
import hashlib
import logging
import re
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any, Optional
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
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
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
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

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


async def get_session_by_refresh_token(db: AsyncSession, token: str) -> Optional[UserSession]:
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


def make_login_attempt_identifier(email: str, ip_address: Optional[str]) -> str:
    normalized_email = email.strip().lower()
    normalized_ip = (ip_address or "unknown").strip().lower()
    digest = hashlib.sha256(f"{normalized_email}|{normalized_ip}".encode("utf-8")).hexdigest()
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
    await _redis_setex(_auth_key("verify", token), settings.EMAIL_VERIFICATION_TTL_SECONDS, payload)
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
    await _redis_setex(_auth_key("reset", token), settings.PASSWORD_RESET_TTL_SECONDS, payload)
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
    return f"{_normalize_base_url(settings.FRONTEND_BASE_URL)}/auth/verify-email?token={token}"


def build_password_reset_url(token: str) -> str:
    return f"{_normalize_base_url(settings.FRONTEND_BASE_URL)}/auth/reset-password?token={token}"


def _send_email_sync(to_email: str, subject: str, text: str) -> None:
    msg = EmailMessage()
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(text)

    if not settings.SMTP_HOST:
        logger.info("SMTP is not configured. Email to %s: %s\n%s", to_email, subject, text)
        return

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)


async def send_auth_email(to_email: str, subject: str, text: str) -> None:
    try:
        await asyncio.to_thread(_send_email_sync, to_email, subject, text)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send auth email to %s", to_email)


async def send_email_verification_email(to_email: str, token: str) -> None:
    verification_url = build_email_verification_url(token)
    subject = "Verify your Stellalink email"
    text = (
        "Please verify your email for Stellalink.\n\n"
        f"Open this link: {verification_url}\n\n"
        f"This link expires in {settings.EMAIL_VERIFICATION_TTL_SECONDS // 3600} hours."
    )
    await send_auth_email(to_email, subject, text)


async def send_password_reset_email(to_email: str, token: str) -> None:
    reset_url = build_password_reset_url(token)
    subject = "Reset your Stellalink password"
    text = (
        "We received a password reset request for your Stellalink account.\n\n"
        f"Open this link: {reset_url}\n\n"
        f"This link expires in {settings.PASSWORD_RESET_TTL_SECONDS // 60} minutes.\n"
        "If you did not request this, you can ignore this email."
    )
    await send_auth_email(to_email, subject, text)
