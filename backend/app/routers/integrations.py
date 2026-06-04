from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.integration import (
    CodeProviderOAuthStartRequest,
    CodeProviderTokenConnectRequest,
    IntegrationsResponse,
    OAuthStartResponse,
    SteamOpenIdStartResponse,
)
from app.services import profile as profile_svc
from app.services.external_integrations import (
    ExternalApiError,
    connect_code_provider_oauth_response,
    connect_code_provider_token,
    connect_spotify_oauth_response,
    connect_steam_openid_response,
    create_code_provider_oauth_url,
    create_spotify_oauth_url,
    create_steam_openid_auth_url,
    disconnect_code_provider_account,
    disconnect_spotify_account,
    disconnect_steam_account,
    get_connected_account,
    integrations_response,
    spotify_realtime_response,
    sync_code_provider_account,
    sync_spotify_account,
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


@router.post("/code/token", response_model=IntegrationsResponse)
async def connect_code_provider_by_token(
    body: CodeProviderTokenConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await connect_code_provider_token(
            db, current_user.id, body.provider, body.access_token, body.base_url
        )
    except ExternalApiError as exc:
        _raise_api_error(exc)
    return await integrations_response(db, current_user.id)


@router.post("/code/oauth/start", response_model=OAuthStartResponse)
async def start_code_provider_oauth(
    body: CodeProviderOAuthStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        auth_url = await create_code_provider_oauth_url(
            db, current_user.id, body.provider, body.base_url
        )
    except ExternalApiError as exc:
        _raise_api_error(exc)
    return OAuthStartResponse(auth_url=auth_url)


@router.get("/code/oauth/callback")
async def code_provider_oauth_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    redirect_url = await connect_code_provider_oauth_response(
        db, dict(request.query_params.multi_items())
    )
    return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)


@router.post("/spotify/oauth/start", response_model=OAuthStartResponse)
async def start_spotify_oauth(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        auth_url = await create_spotify_oauth_url(db, current_user.id)
    except ExternalApiError as exc:
        _raise_api_error(exc)
    return OAuthStartResponse(auth_url=auth_url)


@router.get("/spotify/oauth/callback")
async def spotify_oauth_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    redirect_url = await connect_spotify_oauth_response(
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


@router.post("/spotify/sync", response_model=IntegrationsResponse)
async def sync_spotify(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await sync_spotify_account(db, current_user.id)
    except ExternalApiError as exc:
        _raise_api_error(exc)
    return await integrations_response(db, current_user.id)


@router.get("/spotify/playback")
async def read_spotify_playback(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await get_connected_account(db, current_user.id, "spotify")
    if not account:
        raise HTTPException(status_code=404, detail="Spotify account is not connected.")
    return await spotify_realtime_response(db, account)


@router.get("/spotify/public/{slug}/playback")
async def read_public_spotify_playback(slug: str, db: AsyncSession = Depends(get_db)):
    profile = await profile_svc.get_profile_by_slug(db, slug)
    if not profile or profile.status == "draft" or not profile.user:
        raise HTTPException(status_code=404, detail="Profile not found")
    account = next(
        (
            account
            for account in profile.user.connected_accounts
            if account.provider == "spotify" and account.is_active
        ),
        None,
    )
    if not account:
        raise HTTPException(status_code=404, detail="Spotify account is not connected.")
    return await spotify_realtime_response(db, account)


@router.post("/code/{provider}/sync", response_model=IntegrationsResponse)
async def sync_code_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await sync_code_provider_account(db, current_user.id, provider)
    except ExternalApiError as exc:
        _raise_api_error(exc)
    return await integrations_response(db, current_user.id)


@router.delete("/steam", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_steam(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await disconnect_steam_account(db, current_user.id)


@router.delete("/spotify", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_spotify(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await disconnect_spotify_account(db, current_user.id)


@router.delete("/code/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_code_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await disconnect_code_provider_account(db, current_user.id, provider)
    except ExternalApiError as exc:
        _raise_api_error(exc)
