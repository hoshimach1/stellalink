from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_admin_user
from app.models.user import User
from app.schemas.admin import (
    AdminActionResponse,
    ApiSettingsResponse,
    ApiSettingsUpdate,
    SmtpSettingsResponse,
    SmtpSettingsUpdate,
    SmtpTestRequest,
)
from app.services.admin_settings import (
    apply_public_auth_settings,
    get_api_settings_response,
    get_smtp_delivery_config,
    get_smtp_response,
    save_api_settings,
    save_smtp_settings,
)
from app.services.auth import send_auth_email

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/smtp-settings", response_model=SmtpSettingsResponse)
async def read_smtp_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    return await get_smtp_response(db)


@router.get("/api-settings", response_model=ApiSettingsResponse)
async def read_api_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    return await get_api_settings_response(db)


@router.put("/api-settings", response_model=ApiSettingsResponse)
async def update_api_settings(
    body: ApiSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    return await save_api_settings(db, body)


@router.put("/smtp-settings", response_model=SmtpSettingsResponse)
async def update_smtp_settings(
    body: SmtpSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    response = await save_smtp_settings(db, body)
    await apply_public_auth_settings(db)
    return response


@router.post("/smtp-settings/test", response_model=AdminActionResponse)
async def send_smtp_test_email(
    body: SmtpTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    delivery = await get_smtp_delivery_config(db)
    recipient = str(body.to_email or current_user.email)
    try:
        await send_auth_email(
            recipient,
            "Stellalink SMTP test",
            "SMTP is configured. This is a test email from Stellalink admin settings.",
            (
                "<p>SMTP is configured.</p>"
                "<p>This is a test email from Stellalink admin settings.</p>"
            ),
            delivery,
            raise_errors=True,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SMTP test failed: {exc}",
        ) from exc

    return AdminActionResponse(detail=f"Test email sent to {recipient}")
