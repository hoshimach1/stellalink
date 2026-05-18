from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.integration import (
    IntegrationsResponse,
    SteamOpenIdStartResponse,
)
from app.services.external_integrations import (
    ExternalApiError,
    connect_steam_openid_response,
    create_steam_openid_auth_url,
    disconnect_steam_account,
    integrations_response,
    sync_steam_account,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


def _raise_api_error(exc: ExternalApiError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/me", response_model=IntegrationsResponse)
async def read_my_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await integrations_response(db, current_user.id)


@router.post("/steam/openid/start", response_model=SteamOpenIdStartResponse)
async def start_steam_openid(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auth_url = await create_steam_openid_auth_url(db, current_user.id)
    return SteamOpenIdStartResponse(auth_url=auth_url)


@router.get("/steam/openid/callback")
async def steam_openid_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    redirect_url = await connect_steam_openid_response(
        db, dict(request.query_params.multi_items())
    )
    return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)


@router.post("/steam/sync", response_model=IntegrationsResponse)
async def sync_steam(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await sync_steam_account(db, current_user.id)
    except ExternalApiError as exc:
        _raise_api_error(exc)
    return await integrations_response(db, current_user.id)


@router.delete("/steam", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_steam(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await disconnect_steam_account(db, current_user.id)
