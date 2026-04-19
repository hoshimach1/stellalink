import math
import os
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RequestEmailVerificationResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth import (
    clear_failed_login_attempts,
    consume_email_verification_token,
    consume_password_reset_token,
    create_email_verification_token,
    create_password_reset_token,
    create_session,
    get_login_lock_ttl_seconds,
    get_session_by_refresh_token,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    make_login_attempt_identifier,
    register_failed_login_attempt,
    revoke_refresh_session,
    revoke_user_sessions,
    send_email_verification_email,
    send_password_reset_email,
    validate_password,
    verify_password,
)

UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads" / "avatars"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if await get_user_by_email(db, body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    password_error = validate_password(body.password)
    if password_error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=password_error)

    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    await db.flush()  # get user.id before commit

    access_token, refresh_token = await create_session(
        db,
        user,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    verify_token = await create_email_verification_token(user.id, user.email)
    await send_email_verification_email(user.email, verify_token)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip_address = request.client.host if request.client else None
    attempt_id = make_login_attempt_identifier(body.email, ip_address)
    lock_ttl = await get_login_lock_ttl_seconds(attempt_id)
    if lock_ttl > 0:
        retry_minutes = max(1, math.ceil(lock_ttl / 60))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Try again in {retry_minutes} minute(s).",
        )

    user = await get_user_by_email(db, body.email)

    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        await register_failed_login_attempt(attempt_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    await clear_failed_login_attempts(attempt_id)

    access_token, refresh_token = await create_session(
        db,
        user,
        user_agent=request.headers.get("user-agent"),
        ip_address=ip_address,
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    session = await get_session_by_refresh_token(db, body.refresh_token)

    if not session or not session.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Rotate: delete old session, issue new tokens
    await db.delete(session)
    access_token, new_refresh = await create_session(
        db,
        session.user,
        user_agent=session.user_agent,
        ip_address=session.ip_address,
    )

    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    await revoke_refresh_session(db, body.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/request-email-verification", response_model=RequestEmailVerificationResponse)
async def request_email_verification(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.email_verified:
        return RequestEmailVerificationResponse(detail="Email is already verified")

    token = await create_email_verification_token(current_user.id, current_user.email)
    await send_email_verification_email(current_user.email, token)

    response = RequestEmailVerificationResponse()
    if settings.AUTH_DEBUG_TOKENS:
        response.verification_token = token
    return response


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(
    body: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    payload = await consume_email_verification_token(body.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    user = await get_user_by_id(db, payload["user_id"])
    if not user or user.email.strip().lower() != payload["email"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification payload",
        )

    if not user.email_verified:
        user.email_verified = True
        db.add(user)
        await db.commit()


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    response = ForgotPasswordResponse()
    user = await get_user_by_email(db, body.email)
    if not user:
        return response

    token = await create_password_reset_token(user.id, user.email)
    await send_password_reset_email(user.email, token)

    if settings.AUTH_DEBUG_TOKENS:
        response.reset_token = token

    return response


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    password_error = validate_password(body.new_password)
    if password_error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=password_error)

    payload = await consume_password_reset_token(body.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = await get_user_by_id(db, payload["user_id"])
    if not user or user.email.strip().lower() != payload["email"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset payload")

    if user.password_hash and verify_password(body.new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    user.password_hash = hash_password(body.new_password)
    db.add(user)
    await db.commit()

    # Revoke all active sessions after password reset.
    await revoke_user_sessions(db, user.id)


@router.post("/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="Unsupported avatar format. Allowed: JPEG, PNG, WebP, GIF")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Avatar is too large. Maximum size is 5 MB")

    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    filename = f"{current_user.id}{ext}"
    dest = UPLOADS_DIR / filename

    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)

    current_user.avatar_url = f"/uploads/avatars/{filename}"
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.delete("/avatar", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avatar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.avatar_url:
        filename = current_user.avatar_url.rsplit("/", 1)[-1]
        dest = UPLOADS_DIR / filename
        if dest.exists():
            dest.unlink()
    current_user.avatar_url = None
    db.add(current_user)
    await db.commit()


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.password_hash or not verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    password_error = validate_password(body.new_password)
    if password_error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=password_error)

    if verify_password(body.new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    current_user.password_hash = hash_password(body.new_password)
    db.add(current_user)
    await db.commit()

    # Revoke every session except the current one passed from client.
    await revoke_user_sessions(db, current_user.id, exclude_refresh_token=body.refresh_token)
