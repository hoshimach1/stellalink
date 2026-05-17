import asyncio
import json
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.integration import ConnectedAccount
from app.redis import get_redis
from app.schemas.integration import (
    ConnectedAccountResponse,
    IntegrationCapabilities,
    IntegrationsResponse,
)
from app.services.admin_settings import get_api_settings_data

STEAM_ID64_RE = re.compile(r"^\d{17}$")
STEAM_VANITY_RE = re.compile(r"^[A-Za-z0-9_-]{2,64}$")
STEAM_API_BASE = "https://api.steampowered.com"
STEAM_OPENID_LOGIN_URL = "https://steamcommunity.com/openid/login"
STEAM_OPENID_STATE_TTL_SECONDS = 600
FACEIT_API_BASE = "https://open.faceit.com/data/v4"
FACEIT_GAME_ID = "cs2"


class ExternalApiError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _hinted_error(service: str, status_code: int, body: str = "") -> ExternalApiError:
    if status_code == 401 or status_code == 403:
        return ExternalApiError(f"{service}: API key was rejected.", status_code=502)
    if status_code == 404:
        return ExternalApiError(
            f"{service}: requested profile was not found.", status_code=404
        )
    if status_code == 429:
        return ExternalApiError(f"{service}: rate limit exceeded.", status_code=429)
    details = body[:180].strip()
    suffix = f" {details}" if details else ""
    return ExternalApiError(
        f"{service}: upstream request failed with {status_code}.{suffix}",
        status_code=502,
    )


def _read_json(
    url: str, service: str, headers: Optional[dict[str, str]] = None, timeout: int = 12
) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed trusted API hosts
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise _hinted_error(service, exc.code, body) from exc
    except urllib.error.URLError as exc:
        raise ExternalApiError(f"{service}: network request failed.") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ExternalApiError(f"{service}: returned invalid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ExternalApiError(f"{service}: returned an unexpected payload.")
    return parsed


async def _fetch_json(
    url: str,
    service: str,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 12,
) -> dict[str, Any]:
    return await asyncio.to_thread(_read_json, url, service, headers, timeout)


def _read_text_post(
    url: str, data: dict[str, str], service: str, timeout: int = 12
) -> str:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed trusted API host
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise _hinted_error(service, exc.code, body) from exc
    except urllib.error.URLError as exc:
        raise ExternalApiError(f"{service}: network request failed.") from exc


async def _post_text(
    url: str, data: dict[str, str], service: str, timeout: int = 12
) -> str:
    return await asyncio.to_thread(_read_text_post, url, data, service, timeout)


def _steam_url(path: str, params: dict[str, Any]) -> str:
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    return f"{STEAM_API_BASE}{path}?{query}"


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _hours(minutes: Any) -> float:
    return round((_to_int(minutes) / 60) * 10) / 10


def _steam_app_header_url(app_id: Any) -> Optional[str]:
    app_id_int = _to_int(app_id)
    if app_id_int <= 0:
        return None
    return f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id_int}/header.jpg"


def _timestamp_to_iso(value: Any) -> Optional[str]:
    timestamp = _to_int(value)
    if timestamp <= 0:
        return None
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


def _faceit_url(path: str, params: Optional[dict[str, Any]] = None) -> str:
    query = urllib.parse.urlencode(params or {})
    return f"{FACEIT_API_BASE}{path}{f'?{query}' if query else ''}"


def _steam_openid_state_key(state: str) -> str:
    return f"integration:steam_openid:{state}"


def _frontend_base_url() -> str:
    return settings.FRONTEND_BASE_URL.rstrip("/")


def _steam_openid_callback_url(state: str) -> str:
    return f"{_frontend_base_url()}/api/integrations/steam/openid/callback?{urllib.parse.urlencode({'state': state})}"


def _steam_openid_result_url(success: bool, detail: Optional[str] = None) -> str:
    query = {"tab": "integrations", "steam": "connected" if success else "error"}
    if detail and not success:
        query["steam_error"] = detail[:160]
    return f"{_frontend_base_url()}/dashboard?{urllib.parse.urlencode(query)}"


async def create_steam_openid_auth_url(user_id: UUID) -> str:
    state = secrets.token_urlsafe(32)
    redis = await get_redis()
    await redis.setex(
        _steam_openid_state_key(state), STEAM_OPENID_STATE_TTL_SECONDS, str(user_id)
    )

    return_to = _steam_openid_callback_url(state)
    realm = _frontend_base_url()
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": return_to,
        "openid.realm": realm,
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }
    return f"{STEAM_OPENID_LOGIN_URL}?{urllib.parse.urlencode(params)}"


async def consume_steam_openid_state(state: str) -> Optional[UUID]:
    redis = await get_redis()
    key = _steam_openid_state_key(state)
    raw_user_id = await redis.get(key)
    if not raw_user_id:
        return None
    await redis.delete(key)
    try:
        return UUID(str(raw_user_id))
    except ValueError:
        return None


async def verify_steam_openid_response(query: dict[str, str]) -> str:
    if query.get("openid.mode") != "id_res":
        raise ExternalApiError(
            "Steam sign-in was cancelled or returned an invalid response.", 400
        )

    verification_payload = {
        key: value for key, value in query.items() if key.startswith("openid.")
    }
    verification_payload["openid.mode"] = "check_authentication"

    response = await _post_text(
        STEAM_OPENID_LOGIN_URL, verification_payload, "Steam OpenID"
    )
    values = dict(line.split(":", 1) for line in response.splitlines() if ":" in line)
    if values.get("is_valid") != "true":
        raise ExternalApiError("Steam OpenID verification failed.", 400)

    claimed_id = query.get("openid.claimed_id") or query.get("openid.identity") or ""
    match = re.match(
        r"^https?://steamcommunity\.com/openid/id/(\d{17,25})/?$", claimed_id
    )
    if not match:
        raise ExternalApiError(
            "Steam OpenID response did not include a valid SteamID64.", 400
        )
    return match.group(1)


async def connect_steam_openid_response(db: AsyncSession, query: dict[str, str]) -> str:
    state = _clean_text(query.get("state"))
    if not state:
        return _steam_openid_result_url(False, "Missing Steam sign-in state.")

    user_id = await consume_steam_openid_state(state)
    if not user_id:
        return _steam_openid_result_url(False, "Steam sign-in expired. Try again.")

    try:
        steam_id = await verify_steam_openid_response(query)
        await connect_steam_account(db, user_id, steam_id)
    except ExternalApiError as exc:
        return _steam_openid_result_url(False, str(exc))

    return _steam_openid_result_url(True)


def _extract_steam_identifier(raw: str) -> str:
    value = raw.strip()
    parsed = urllib.parse.urlparse(value if "://" in value else f"https://{value}")
    if parsed.netloc and "steamcommunity.com" in parsed.netloc.lower():
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0].lower() in {"profiles", "id"}:
            return parts[1]
    return value.rstrip("/")


async def resolve_steam_id(raw: str, api_key: Optional[str]) -> str:
    candidate = _extract_steam_identifier(raw)
    if STEAM_ID64_RE.match(candidate):
        return candidate

    if not STEAM_VANITY_RE.match(candidate):
        raise ExternalApiError(
            "Steam ID must be a SteamID64, vanity name, or steamcommunity.com URL.", 400
        )
    if not api_key:
        raise ExternalApiError(
            "Steam API key is required to resolve a vanity Steam URL.", 400
        )

    url = _steam_url(
        "/ISteamUser/ResolveVanityURL/v1/",
        {"key": api_key, "vanityurl": candidate},
    )
    payload = await _fetch_json(url, "Steam")
    response = (
        payload.get("response") if isinstance(payload.get("response"), dict) else {}
    )
    if response.get("success") != 1 or not response.get("steamid"):
        raise ExternalApiError("Steam vanity URL was not found.", 404)
    return str(response["steamid"])


async def fetch_steam_profile(api_key: str, steam_id: str) -> Optional[dict[str, Any]]:
    payload = await _fetch_json(
        _steam_url(
            "/ISteamUser/GetPlayerSummaries/v2/",
            {"key": api_key, "steamids": steam_id},
        ),
        "Steam",
    )
    players = (payload.get("response") or {}).get("players") or []
    return players[0] if players else None


async def fetch_recent_games(
    api_key: str, steam_id: str, count: int = 5
) -> list[dict[str, Any]]:
    recent_payload, owned_result = await asyncio.gather(
        _fetch_json(
            _steam_url(
                "/IPlayerService/GetRecentlyPlayedGames/v1/",
                {
                    "key": api_key,
                    "steamid": steam_id,
                    "count": count,
                    "format": "json",
                },
            ),
            "Steam",
        ),
        fetch_owned_games(api_key, steam_id),
        return_exceptions=True,
    )
    if isinstance(recent_payload, Exception):
        raise recent_payload
    owned_games = [] if isinstance(owned_result, Exception) else owned_result
    games = (recent_payload.get("response") or {}).get("games") or []
    owned_by_app_id = {
        _to_int(game.get("appid")): game
        for game in owned_games
        if isinstance(game, dict)
    }
    result = []
    for game in games:
        if not isinstance(game, dict):
            continue
        app_id = _to_int(game.get("appid"))
        owned = owned_by_app_id.get(app_id, {})
        recent_minutes = _to_int(game.get("playtime_2weeks"))
        total_minutes = _to_int(
            owned.get("playtime_forever"), _to_int(game.get("playtime_forever"))
        )
        last_played_ts = _to_int(owned.get("rtime_last_played"))
        result.append(
            {
                "appid": app_id,
                "name": game.get("name"),
                "playtime_2weeks": recent_minutes,
                "playtime_forever": total_minutes,
                "playtime_recent_minutes": recent_minutes,
                "playtime_total_minutes": total_minutes,
                "recent_hours": _hours(recent_minutes),
                "total_hours": _hours(total_minutes),
                "last_played_ts": last_played_ts or None,
                "last_played_at": _timestamp_to_iso(last_played_ts),
                "img_icon_url": game.get("img_icon_url") or owned.get("img_icon_url"),
                "header_image": _steam_app_header_url(app_id),
                "source": "recent",
            }
        )
    if result:
        return result[:count]

    fallback_games = sorted(
        (game for game in owned_games if _to_int(game.get("rtime_last_played")) > 0),
        key=lambda game: _to_int(game.get("rtime_last_played")),
        reverse=True,
    )
    for game in fallback_games[:count]:
        app_id = _to_int(game.get("appid"))
        total_minutes = _to_int(game.get("playtime_forever"))
        last_played_ts = _to_int(game.get("rtime_last_played"))
        result.append(
            {
                "appid": app_id,
                "name": game.get("name"),
                "playtime_2weeks": _to_int(game.get("playtime_2weeks")),
                "playtime_forever": total_minutes,
                "playtime_recent_minutes": _to_int(game.get("playtime_2weeks")),
                "playtime_total_minutes": total_minutes,
                "recent_hours": _hours(game.get("playtime_2weeks")),
                "total_hours": _hours(total_minutes),
                "last_played_ts": last_played_ts,
                "last_played_at": _timestamp_to_iso(last_played_ts),
                "img_icon_url": game.get("img_icon_url"),
                "header_image": _steam_app_header_url(app_id),
                "source": "owned",
            }
        )
    return result


async def fetch_owned_games(api_key: str, steam_id: str) -> list[dict[str, Any]]:
    payload = await _fetch_json(
        _steam_url(
            "/IPlayerService/GetOwnedGames/v1/",
            {
                "key": api_key,
                "steamid": steam_id,
                "include_appinfo": "true",
                "include_played_free_games": "true",
                "format": "json",
            },
        ),
        "Steam",
    )
    games = (payload.get("response") or {}).get("games") or []
    return [game for game in games if isinstance(game, dict)]


async def fetch_steam_level(api_key: str, steam_id: str) -> Optional[int]:
    payload = await _fetch_json(
        _steam_url(
            "/IPlayerService/GetSteamLevel/v1/",
            {"key": api_key, "steamid": steam_id, "format": "json"},
        ),
        "Steam",
    )
    level = (payload.get("response") or {}).get("player_level")
    return int(level) if level is not None else None


async def fetch_steam_badges(api_key: str, steam_id: str) -> dict[str, Any]:
    payload = await _fetch_json(
        _steam_url(
            "/IPlayerService/GetBadges/v1/",
            {"key": api_key, "steamid": steam_id, "format": "json"},
        ),
        "Steam",
    )
    response = (
        payload.get("response") if isinstance(payload.get("response"), dict) else {}
    )
    badges = response.get("badges") if isinstance(response.get("badges"), list) else []
    return {
        "badge_count": len(badges),
        "player_xp": response.get("player_xp"),
        "player_level": response.get("player_level"),
        "player_xp_needed_current_level": response.get(
            "player_xp_needed_current_level"
        ),
        "player_xp_needed_to_level_up": response.get("player_xp_needed_to_level_up"),
    }


async def fetch_faceit_profile(
    api_key: str, steam_id: str, game_id: str = FACEIT_GAME_ID
) -> Optional[dict[str, Any]]:
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        player = await _fetch_json(
            _faceit_url("/players", {"game": game_id, "game_player_id": steam_id}),
            "FACEIT",
            headers=headers,
        )
    except ExternalApiError as exc:
        if exc.status_code == 404:
            return None
        raise

    player_id = _clean_text(player.get("player_id"))
    stats_payload: dict[str, Any] = {}
    if player_id:
        try:
            stats_payload = await _fetch_json(
                _faceit_url(f"/players/{player_id}/stats/{game_id}"),
                "FACEIT",
                headers=headers,
            )
        except ExternalApiError as exc:
            stats_payload = {"sync_error": str(exc)}

    return _summarize_faceit_player(player, stats_payload, game_id)


def _summarize_faceit_player(
    player: dict[str, Any], stats_payload: dict[str, Any], game_id: str
) -> dict[str, Any]:
    games = player.get("games") if isinstance(player.get("games"), dict) else {}
    game = games.get(game_id) if isinstance(games.get(game_id), dict) else {}
    lifetime = (
        stats_payload.get("lifetime")
        if isinstance(stats_payload.get("lifetime"), dict)
        else {}
    )

    return {
        "available": True,
        "source": "steam",
        "game": game_id,
        "player_id": player.get("player_id"),
        "nickname": player.get("nickname"),
        "avatar": player.get("avatar"),
        "country": player.get("country"),
        "faceit_url": player.get("faceit_url"),
        "verified": player.get("verified"),
        "steam_id_64": player.get("steam_id_64"),
        "steam_nickname": player.get("steam_nickname"),
        "skill_level": game.get("skill_level"),
        "skill_level_label": game.get("skill_level_label"),
        "faceit_elo": game.get("faceit_elo"),
        "region": game.get("region"),
        "game_player_name": game.get("game_player_name"),
        "stats": {
            "matches": lifetime.get("Matches"),
            "wins": lifetime.get("Wins"),
            "win_rate": lifetime.get("Win Rate %"),
            "kd": lifetime.get("Average K/D Ratio") or lifetime.get("K/D Ratio"),
            "headshots": lifetime.get("Average Headshots %")
            or lifetime.get("Total Headshots %"),
            "recent_results": lifetime.get("Recent Results"),
        },
        "stats_error": stats_payload.get("sync_error"),
    }


def unavailable_inventory_highlight(app_id: int, context_id: str) -> dict[str, Any]:
    return {
        "available": False,
        "app_id": app_id,
        "context_id": context_id,
        "title": "Market price is unavailable",
        "reason": (
            "Official Steam Web API inventory access requires a publisher key with Economy permissions, "
            "and regular inventory responses do not include Community Market prices."
        ),
    }


async def build_steam_metadata(
    db: AsyncSession, steam_id: str
) -> tuple[dict[str, Any], Optional[str]]:
    api_settings = await get_api_settings_data(db)
    steam_key = _clean_text(api_settings.get("steam_api_key"))
    faceit_key = _clean_text(api_settings.get("faceit_api_key"))
    app_id = int(api_settings.get("steam_inventory_app_id") or 730)
    context_id = str(api_settings.get("steam_inventory_context_id") or "2")
    now = datetime.now(timezone.utc).isoformat()

    metadata: dict[str, Any] = {
        "steam_id": steam_id,
        "synced_at": now,
        "steam_profile": None,
        "recent_games": [],
        "profile_stats": {},
        "inventory_highlight": unavailable_inventory_highlight(app_id, context_id),
        "faceit_profile": None,
        "errors": [],
    }

    if not steam_key:
        metadata["errors"].append("Steam API key is not configured.")
        return metadata, "Steam API key is not configured."

    sync_errors: list[str] = []

    try:
        metadata["steam_profile"] = await fetch_steam_profile(steam_key, steam_id)
    except ExternalApiError as exc:
        sync_errors.append(str(exc))

    try:
        metadata["recent_games"] = await fetch_recent_games(steam_key, steam_id)
    except ExternalApiError as exc:
        sync_errors.append(str(exc))

    try:
        level = await fetch_steam_level(steam_key, steam_id)
        badges = await fetch_steam_badges(steam_key, steam_id)
        metadata["profile_stats"] = {
            "level": level if level is not None else badges.get("player_level"),
            **badges,
        }
    except ExternalApiError as exc:
        sync_errors.append(str(exc))

    if faceit_key:
        try:
            metadata["faceit_profile"] = await fetch_faceit_profile(
                faceit_key, steam_id
            )
        except ExternalApiError as exc:
            sync_errors.append(str(exc))
    else:
        metadata["faceit_note"] = "FACEIT API key is not configured."

    metadata["errors"] = sync_errors
    return metadata, "; ".join(sync_errors) or None


async def list_connected_accounts(
    db: AsyncSession, user_id: UUID
) -> list[ConnectedAccount]:
    result = await db.execute(
        select(ConnectedAccount)
        .where(ConnectedAccount.user_id == user_id)
        .order_by(ConnectedAccount.created_at)
    )
    return list(result.scalars().all())


async def get_connected_account(
    db: AsyncSession, user_id: UUID, provider: str
) -> Optional[ConnectedAccount]:
    result = await db.execute(
        select(ConnectedAccount)
        .where(
            ConnectedAccount.user_id == user_id,
            ConnectedAccount.provider == provider,
            ConnectedAccount.is_active.is_(True),
        )
        .order_by(ConnectedAccount.updated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def upsert_single_provider_account(
    db: AsyncSession,
    user_id: UUID,
    provider: str,
    provider_uid: str,
    display_name: Optional[str],
    metadata: dict[str, Any],
    sync_error: Optional[str],
) -> ConnectedAccount:
    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user_id,
            ConnectedAccount.provider == provider,
        )
    )
    accounts = list(result.scalars().all())
    account = accounts[0] if accounts else None

    if account is None:
        account = ConnectedAccount(
            user_id=user_id,
            provider=provider,
            provider_uid=provider_uid,
        )
        db.add(account)

    for duplicate in accounts[1:]:
        await db.delete(duplicate)

    now = datetime.now(timezone.utc)
    account.provider_uid = provider_uid
    account.display_name = display_name
    account.account_metadata = metadata
    account.is_active = True
    account.last_synced_at = now
    account.sync_error = sync_error
    account.updated_at = now
    db.add(account)
    return account


async def connect_steam_account(
    db: AsyncSession, user_id: UUID, raw_steam_id: str
) -> ConnectedAccount:
    api_settings = await get_api_settings_data(db)
    steam_key = _clean_text(api_settings.get("steam_api_key"))
    steam_id = await resolve_steam_id(raw_steam_id, steam_key)
    metadata, sync_error = await build_steam_metadata(db, steam_id)
    steam_profile = (
        metadata.get("steam_profile")
        if isinstance(metadata.get("steam_profile"), dict)
        else {}
    )
    display_name = _clean_text(steam_profile.get("personaname")) or steam_id

    account = await upsert_single_provider_account(
        db,
        user_id,
        "steam",
        steam_id,
        display_name,
        metadata,
        sync_error,
    )

    faceit_profile = metadata.get("faceit_profile")
    if isinstance(faceit_profile, dict) and faceit_profile.get("player_id"):
        await upsert_single_provider_account(
            db,
            user_id,
            "faceit",
            str(faceit_profile["player_id"]),
            _clean_text(faceit_profile.get("nickname")),
            faceit_profile,
            _clean_text(faceit_profile.get("stats_error")),
        )

    await db.commit()
    await db.refresh(account)
    return account


async def sync_steam_account(db: AsyncSession, user_id: UUID) -> ConnectedAccount:
    account = await get_connected_account(db, user_id, "steam")
    if not account:
        raise ExternalApiError("Steam account is not connected.", 404)
    return await connect_steam_account(db, user_id, account.provider_uid)


async def disconnect_steam_account(db: AsyncSession, user_id: UUID) -> None:
    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user_id,
            ConnectedAccount.provider.in_(["steam", "faceit"]),
        )
    )
    for account in result.scalars().all():
        await db.delete(account)
    await db.commit()


def account_to_response(account: ConnectedAccount) -> ConnectedAccountResponse:
    metadata = (
        account.account_metadata if isinstance(account.account_metadata, dict) else {}
    )
    return ConnectedAccountResponse(
        id=account.id,
        provider=account.provider,
        provider_uid=account.provider_uid,
        display_name=account.display_name,
        is_active=account.is_active,
        last_synced_at=account.last_synced_at,
        sync_error=account.sync_error,
        metadata=metadata,
    )


async def integrations_response(
    db: AsyncSession, user_id: UUID
) -> IntegrationsResponse:
    accounts = await list_connected_accounts(db, user_id)
    api_settings = await get_api_settings_data(db)
    return IntegrationsResponse(
        accounts=[account_to_response(account) for account in accounts],
        capabilities=IntegrationCapabilities(
            steam_api_key_set=bool(_clean_text(api_settings.get("steam_api_key"))),
            faceit_api_key_set=bool(_clean_text(api_settings.get("faceit_api_key"))),
            steam_inventory_prices_supported=False,
        ),
    )
