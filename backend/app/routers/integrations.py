from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.integration import IntegrationsResponse, SteamConnectRequest
from app.services.external_integrations import (
    ExternalApiError,
    connect_steam_account,
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


@router.put("/steam", response_model=IntegrationsResponse)
async def connect_steam(
    body: SteamConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await connect_steam_account(db, current_user.id, body.steam_id)
    except ExternalApiError as exc:
        _raise_api_error(exc)
    return await integrations_response(db, current_user.id)


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
