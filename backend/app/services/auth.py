import secrets
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.user import User, UserSession

ALGORITHM = "HS256"


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
