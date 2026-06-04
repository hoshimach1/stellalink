import asyncio
import base64
import json
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integration import ConnectedAccount
from app.redis import get_redis
from app.schemas.integration import (
    ConnectedAccountResponse,
    IntegrationCapabilities,
    IntegrationsResponse,
)
from app.services.admin_settings import (
    get_api_settings_data,
    get_public_frontend_base_url,
)

STEAM_ID64_RE = re.compile(r"^\d{17}$")
STEAM_VANITY_RE = re.compile(r"^[A-Za-z0-9_-]{2,64}$")
STEAM_API_BASE = "https://api.steampowered.com"
STEAM_OPENID_LOGIN_URL = "https://steamcommunity.com/openid/login"
STEAM_OPENID_STATE_TTL_SECONDS = 600
FACEIT_API_BASE = "https://open.faceit.com/data/v4"
FACEIT_GAME_ID = "cs2"
CODE_OAUTH_STATE_TTL_SECONDS = 600
CODE_PROVIDERS = {"github", "gitlab", "gitea"}
CODE_PROVIDER_DEFAULT_BASE_URLS = {
    "github": "https://github.com",
    "gitlab": "https://gitlab.com",
    "gitea": "https://gitea.com",
}
CODE_PROVIDER_LABELS = {
    "github": "GitHub",
    "gitlab": "GitLab",
    "gitea": "Gitea",
}
CODE_PROVIDER_SCOPES = {
    "github": "read:user repo",
    "gitlab": "read_user read_api",
    "gitea": "read:user read:repository",
}
CODE_PROVIDER_ACTIVITY_DAYS = 90
SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_ACCOUNTS_BASE = "https://accounts.spotify.com"
SPOTIFY_OAUTH_STATE_TTL_SECONDS = 600
SPOTIFY_SCOPES = (
    "user-read-currently-playing "
    "user-read-playback-state "
    "user-read-recently-played "
    "user-top-read"
)


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
        if service == "GitLab":
            return ExternalApiError(
                "GitLab: token was rejected. Use a Personal Access Token "
                "with read_api and read_user scopes.",
                status_code=400,
            )
        return ExternalApiError(
            f"{service}: API key was rejected or lacks required permissions.",
            status_code=400,
        )
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


def _read_json_value(
    url: str, service: str, headers: Optional[dict[str, str]] = None, timeout: int = 12
) -> Any:
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
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ExternalApiError(f"{service}: returned invalid JSON.") from exc


def _read_optional_json(
    url: str, service: str, headers: Optional[dict[str, str]] = None, timeout: int = 12
) -> Optional[dict[str, Any]]:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed trusted API hosts
            if response.status == 204:
                return None
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 204:
            return None
        body = exc.read().decode("utf-8", errors="replace")
        raise _hinted_error(service, exc.code, body) from exc
    except urllib.error.URLError as exc:
        raise ExternalApiError(f"{service}: network request failed.") from exc

    if not raw.strip():
        return None
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


async def _fetch_json_value(
    url: str,
    service: str,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 12,
) -> Any:
    return await asyncio.to_thread(_read_json_value, url, service, headers, timeout)


async def _fetch_optional_json(
    url: str,
    service: str,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 12,
) -> Optional[dict[str, Any]]:
    return await asyncio.to_thread(_read_optional_json, url, service, headers, timeout)


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


def _read_json_post(
    url: str,
    data: dict[str, str],
    service: str,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 12,
) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    request_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        **(headers or {}),
    }
    request = urllib.request.Request(
        url, data=encoded, headers=request_headers, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - OAuth endpoints are selected from configured provider hosts
            raw = response.read().decode("utf-8", errors="replace")
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


async def _post_json(
    url: str,
    data: dict[str, str],
    service: str,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 12,
) -> dict[str, Any]:
    return await asyncio.to_thread(
        _read_json_post, url, data, service, headers, timeout
    )


def _read_json_body_post(
    url: str,
    payload: dict[str, Any],
    service: str,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 12,
) -> dict[str, Any]:
    encoded = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        **(headers or {}),
    }
    request = urllib.request.Request(
        url, data=encoded, headers=request_headers, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed trusted API hosts
            raw = response.read().decode("utf-8", errors="replace")
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


async def _post_json_body(
    url: str,
    payload: dict[str, Any],
    service: str,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 12,
) -> dict[str, Any]:
    return await asyncio.to_thread(
        _read_json_body_post, url, payload, service, headers, timeout
    )


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


def _steam_openid_callback_url(frontend_base_url: str, state: str) -> str:
    query = urllib.parse.urlencode({"state": state})
    return f"{frontend_base_url}/api/integrations/steam/openid/callback?{query}"


def _steam_openid_result_url(
    frontend_base_url: str, success: bool, detail: Optional[str] = None
) -> str:
    query = {"tab": "integrations", "steam": "connected" if success else "error"}
    if detail and not success:
        query["steam_error"] = detail[:160]
    return f"{frontend_base_url}/dashboard?{urllib.parse.urlencode(query)}"


def _code_oauth_state_key(state: str) -> str:
    return f"integration:code_oauth:{state}"


def _provider_label(provider: str) -> str:
    return CODE_PROVIDER_LABELS.get(provider, provider)


def _normalize_code_provider(provider: str) -> str:
    provider = provider.strip().lower()
    if provider not in CODE_PROVIDERS:
        raise ExternalApiError("Unsupported code provider.", 400)
    return provider


def _normalize_base_url(provider: str, raw_base_url: Optional[str]) -> str:
    base_url = _clean_text(raw_base_url) or CODE_PROVIDER_DEFAULT_BASE_URLS[provider]
    parsed = urllib.parse.urlparse(base_url)
    if not parsed.scheme:
        parsed = urllib.parse.urlparse(f"https://{base_url}")

    host = parsed.hostname or ""
    is_local = host in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme not in {"http", "https"}:
        raise ExternalApiError("Provider URL must start with http:// or https://.", 400)
    if parsed.scheme != "https" and not is_local:
        raise ExternalApiError("Self-hosted provider URL must use HTTPS.", 400)

    normalized = urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", "")
    ).rstrip("/")
    return normalized or CODE_PROVIDER_DEFAULT_BASE_URLS[provider]


def _is_default_code_provider_base_url(provider: str, base_url: str) -> bool:
    return base_url == CODE_PROVIDER_DEFAULT_BASE_URLS[provider]


def _code_provider_urls(provider: str, base_url: str) -> dict[str, str]:
    if provider == "github":
        api_base = (
            "https://api.github.com"
            if base_url == CODE_PROVIDER_DEFAULT_BASE_URLS["github"]
            else f"{base_url}/api/v3"
        )
        return {
            "authorize": f"{base_url}/login/oauth/authorize",
            "token": f"{base_url}/login/oauth/access_token",
            "api": api_base,
        }
    if provider == "gitlab":
        return {
            "authorize": f"{base_url}/oauth/authorize",
            "token": f"{base_url}/oauth/token",
            "api": f"{base_url}/api/v4",
        }
    return {
        "authorize": f"{base_url}/login/oauth/authorize",
        "token": f"{base_url}/login/oauth/access_token",
        "api": f"{base_url}/api/v1",
    }


def _code_oauth_callback_url(frontend_base_url: str) -> str:
    return f"{frontend_base_url}/api/integrations/code/oauth/callback"


def _code_provider_result_url(
    frontend_base_url: str,
    provider: str,
    success: bool,
    detail: Optional[str] = None,
) -> str:
    query = {
        "tab": "integrations",
        "integration": provider,
        "integration_status": "connected" if success else "error",
    }
    if detail and not success:
        query["integration_error"] = detail[:160]
    return f"{frontend_base_url}/dashboard?{urllib.parse.urlencode(query)}"


def _token_expires_at(expires_in: Any) -> Optional[datetime]:
    seconds = _to_int(expires_in)
    if seconds <= 0:
        return None
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


def _code_provider_auth_headers(
    provider: str, access_token: str, auth_method: str
) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if provider == "github":
        headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
    elif provider == "gitlab" and auth_method == "token":
        headers["PRIVATE-TOKEN"] = access_token
    elif provider == "gitea" and auth_method == "token":
        headers["Authorization"] = f"token {access_token}"
    else:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _alternate_code_provider_auth_method(
    provider: str, auth_method: str
) -> Optional[str]:
    if provider in {"gitlab", "gitea"}:
        return "oauth" if auth_method == "token" else "token"
    return None


def _looks_like_auth_rejection(exc: ExternalApiError) -> bool:
    return "API key was rejected" in str(exc)


def _summarize_code_provider_user(
    provider: str, base_url: str, api_base: str, payload: dict[str, Any]
) -> dict[str, Any]:
    if provider == "github":
        username = _clean_text(payload.get("login"))
        profile_url = _clean_text(payload.get("html_url"))
    elif provider == "gitlab":
        username = _clean_text(payload.get("username"))
        profile_url = _clean_text(payload.get("web_url"))
    else:
        username = _clean_text(payload.get("login") or payload.get("username"))
        profile_url = _clean_text(payload.get("html_url") or payload.get("website"))

    name = _clean_text(payload.get("name") or payload.get("full_name")) or username
    return {
        "available": True,
        "provider": provider,
        "base_url": base_url,
        "api_base": api_base,
        "uid": str(payload.get("id") or username or ""),
        "username": username,
        "display_name": name,
        "profile_url": profile_url,
        "avatar_url": _clean_text(payload.get("avatar_url")),
        "public_repos": payload.get("public_repos"),
        "followers": payload.get("followers"),
        "following": payload.get("following"),
    }


def _code_repos_url(provider: str, api_base: str, user_id: str) -> str:
    if provider == "github":
        query = urllib.parse.urlencode(
            {
                "per_page": 100,
                "sort": "updated",
                "affiliation": "owner,collaborator,organization_member",
            }
        )
        return f"{api_base}/user/repos?{query}"
    if provider == "gitlab":
        query = urllib.parse.urlencode(
            {
                "membership": "true",
                "per_page": 100,
                "order_by": "last_activity_at",
                "sort": "desc",
            }
        )
        return f"{api_base}/projects?{query}"
    query = urllib.parse.urlencode({"limit": 100})
    return f"{api_base}/user/repos?{query}"


def _github_graphql_url(base_url: str) -> str:
    if base_url == CODE_PROVIDER_DEFAULT_BASE_URLS["github"]:
        return "https://api.github.com/graphql"
    return f"{base_url}/api/graphql"


def _repo_number(repo: dict[str, Any], *keys: str) -> int:
    for key in keys:
        value = repo.get(key)
        if value is not None:
            return _to_int(value)
    return 0


def _repo_bool(repo: dict[str, Any], *keys: str) -> bool:
    return any(bool(repo.get(key)) for key in keys)


def _repo_timestamp(repo: dict[str, Any], provider: str) -> Optional[str]:
    if provider == "github":
        return _clean_text(repo.get("pushed_at") or repo.get("updated_at"))
    if provider == "gitlab":
        return _clean_text(repo.get("last_activity_at"))
    return _clean_text(repo.get("updated_at") or repo.get("created_at"))


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    text = _clean_text(value)
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _empty_contributions(days: int = CODE_PROVIDER_ACTIVITY_DAYS) -> dict[str, Any]:
    days = max(1, min(CODE_PROVIDER_ACTIVITY_DAYS, _to_int(days, 30)))
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=days - 1)
    items = []
    for index in range(days):
        day = start + timedelta(days=index)
        items.append({"date": day.isoformat(), "count": 0, "level": 0})
    return {
        "days": items,
        "total": 0,
        "active_days": 0,
        "window_days": days,
        "from": items[0]["date"] if items else None,
        "to": items[-1]["date"] if items else None,
        "source": "empty",
    }


def _contributions_from_counts(
    counts: dict[str, int],
    days: int = CODE_PROVIDER_ACTIVITY_DAYS,
    source: str = "events",
) -> dict[str, Any]:
    activity = _empty_contributions(days)
    max_count = max(counts.values(), default=0)
    total = 0
    active_days = 0
    for item in activity["days"]:
        count = _to_int(counts.get(item["date"]))
        total += count
        if count > 0:
            active_days += 1
        if count <= 0 or max_count <= 0:
            level = 0
        elif count >= max_count:
            level = 4
        else:
            level = max(1, min(4, int((count / max_count) * 4) + 1))
        item["count"] = count
        item["level"] = level
    activity.update({"total": total, "active_days": active_days, "source": source})
    return activity


def _contributions_from_repositories(
    repositories: list[dict[str, Any]], days: int = CODE_PROVIDER_ACTIVITY_DAYS
) -> dict[str, Any]:
    base = _empty_contributions(days)
    valid_dates = {item["date"] for item in base["days"]}
    counts = {date: 0 for date in valid_dates}
    for repo in repositories:
        if not isinstance(repo, dict):
            continue
        updated_at = _parse_iso_datetime(repo.get("updated_at"))
        if not updated_at:
            continue
        key = updated_at.date().isoformat()
        if key in counts:
            counts[key] += 1
    return _contributions_from_counts(counts, days, "repository_updates")


def _summarize_repo(provider: str, repo: dict[str, Any]) -> dict[str, Any]:
    namespace = repo.get("namespace") if isinstance(repo.get("namespace"), dict) else {}
    owner = repo.get("owner") if isinstance(repo.get("owner"), dict) else {}
    full_name = _clean_text(repo.get("full_name") or repo.get("path_with_namespace"))
    name = (
        _clean_text(repo.get("name") or repo.get("path")) or full_name or "repository"
    )
    if not full_name:
        owner_name = _clean_text(owner.get("login") or owner.get("username"))
        namespace_name = _clean_text(
            namespace.get("full_path") or namespace.get("path")
        )
        full_name = (
            f"{owner_name or namespace_name}/{name}"
            if (owner_name or namespace_name)
            else name
        )

    is_gitlab_private = (
        provider == "gitlab" and _clean_text(repo.get("visibility")) == "private"
    )
    is_gitlab_fork = provider == "gitlab" and isinstance(
        repo.get("forked_from_project"), dict
    )

    return {
        "id": str(repo.get("id") or full_name),
        "name": name,
        "full_name": full_name,
        "url": _clean_text(repo.get("html_url") or repo.get("web_url")),
        "description": _clean_text(repo.get("description")),
        "language": _clean_text(repo.get("language")),
        "stars": _repo_number(repo, "stargazers_count", "star_count", "stars_count"),
        "forks": _repo_number(repo, "forks_count", "forks"),
        "open_issues": _repo_number(repo, "open_issues_count", "open_issues"),
        "is_private": _repo_bool(repo, "private") or is_gitlab_private,
        "is_fork": _repo_bool(repo, "fork") or is_gitlab_fork,
        "is_archived": _repo_bool(repo, "archived"),
        "updated_at": _repo_timestamp(repo, provider),
    }


def _repository_stats(repositories: list[dict[str, Any]]) -> dict[str, Any]:
    language_counts: dict[str, int] = {}
    for repo in repositories:
        language = _clean_text(repo.get("language"))
        if language:
            language_counts[language] = language_counts.get(language, 0) + 1

    top_languages = [
        {"language": language, "repositories": count}
        for language, count in sorted(
            language_counts.items(), key=lambda item: (-item[1], item[0].lower())
        )[:6]
    ]
    last_activity_at = max(
        (str(repo["updated_at"]) for repo in repositories if repo.get("updated_at")),
        default=None,
    )
    return {
        "total_repositories": len(repositories),
        "public_repositories": sum(
            1 for repo in repositories if not repo.get("is_private")
        ),
        "private_repositories": sum(
            1 for repo in repositories if repo.get("is_private")
        ),
        "forked_repositories": sum(1 for repo in repositories if repo.get("is_fork")),
        "archived_repositories": sum(
            1 for repo in repositories if repo.get("is_archived")
        ),
        "stars": sum(_to_int(repo.get("stars")) for repo in repositories),
        "forks": sum(_to_int(repo.get("forks")) for repo in repositories),
        "top_languages": top_languages,
        "last_activity_at": last_activity_at,
    }


async def fetch_github_pinned_repositories(
    base_url: str,
    access_token: str,
    username: str,
    auth_method: str,
    repositories: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not username:
        return []

    payload = await _post_json_body(
        _github_graphql_url(base_url),
        {
            "query": """
query($login: String!) {
  user(login: $login) {
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes {
        ... on Repository {
          id
          name
          nameWithOwner
          url
          description
          primaryLanguage { name }
          stargazerCount
          forkCount
          isPrivate
          isFork
          isArchived
          updatedAt
          pushedAt
        }
      }
    }
  }
}
""",
            "variables": {"login": username},
        },
        "GitHub",
        headers=_code_provider_auth_headers("github", access_token, auth_method),
    )
    if payload.get("errors"):
        raise ExternalApiError("GitHub: pinned repositories request failed.")

    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    user = data.get("user")
    pinned_items = user.get("pinnedItems") if isinstance(user, dict) else {}
    nodes = pinned_items.get("nodes") if isinstance(pinned_items, dict) else []
    if not isinstance(nodes, list):
        return []

    by_full_name = {repo.get("full_name"): repo for repo in repositories}
    result = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        full_name = _clean_text(node.get("nameWithOwner"))
        repo = by_full_name.get(full_name)
        if repo:
            result.append(repo)
            continue
        language = (
            node.get("primaryLanguage")
            if isinstance(node.get("primaryLanguage"), dict)
            else {}
        )
        result.append(
            {
                "id": str(node.get("id") or full_name or node.get("name")),
                "name": _clean_text(node.get("name")) or "repository",
                "full_name": full_name,
                "url": _clean_text(node.get("url")),
                "description": _clean_text(node.get("description")),
                "language": _clean_text(language.get("name")),
                "stars": _to_int(node.get("stargazerCount")),
                "forks": _to_int(node.get("forkCount")),
                "open_issues": 0,
                "is_private": bool(node.get("isPrivate")),
                "is_fork": bool(node.get("isFork")),
                "is_archived": bool(node.get("isArchived")),
                "updated_at": _clean_text(
                    node.get("pushedAt") or node.get("updatedAt")
                ),
            }
        )
    return result


async def fetch_github_contributions(
    base_url: str,
    access_token: str,
    username: str,
    auth_method: str,
    days: int = CODE_PROVIDER_ACTIVITY_DAYS,
) -> dict[str, Any]:
    if not username:
        return _empty_contributions(days)

    now = datetime.now(timezone.utc)
    from_dt = now - timedelta(days=max(1, min(days, CODE_PROVIDER_ACTIVITY_DAYS)) - 1)
    payload = await _post_json_body(
        _github_graphql_url(base_url),
        {
            "query": """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
""",
            "variables": {
                "login": username,
                "from": from_dt.isoformat(),
                "to": now.isoformat(),
            },
        },
        "GitHub",
        headers=_code_provider_auth_headers("github", access_token, auth_method),
    )
    if payload.get("errors"):
        raise ExternalApiError("GitHub: contributions request failed.")

    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    user = data.get("user") if isinstance(data.get("user"), dict) else {}
    collection = user.get("contributionsCollection") if isinstance(user, dict) else {}
    calendar = (
        collection.get("contributionCalendar") if isinstance(collection, dict) else {}
    )
    weeks = calendar.get("weeks") if isinstance(calendar, dict) else []
    counts: dict[str, int] = {}
    if isinstance(weeks, list):
        for week in weeks:
            if not isinstance(week, dict):
                continue
            contribution_days = week.get("contributionDays")
            if not isinstance(contribution_days, list):
                continue
            for day in contribution_days:
                if not isinstance(day, dict):
                    continue
                key = _clean_text(day.get("date"))
                if key:
                    counts[key] = _to_int(day.get("contributionCount"))
    return _contributions_from_counts(counts, days, "github_contribution_calendar")


async def fetch_gitlab_contributions(
    access_token: str,
    api_base: str,
    user_id: str,
    auth_method: str,
    days: int = CODE_PROVIDER_ACTIVITY_DAYS,
) -> dict[str, Any]:
    if not user_id:
        return _empty_contributions(days)

    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=max(1, min(days, CODE_PROVIDER_ACTIVITY_DAYS)) - 1)
    query = urllib.parse.urlencode(
        {
            "after": start.isoformat(),
            "before": today.isoformat(),
            "per_page": 100,
            "sort": "desc",
        }
    )
    url = f"{api_base}/users/{urllib.parse.quote(user_id, safe='')}/events?{query}"
    payload = await _fetch_json_value(
        url,
        "GitLab",
        headers=_code_provider_auth_headers("gitlab", access_token, auth_method),
    )
    if not isinstance(payload, list):
        raise ExternalApiError("GitLab: returned an unexpected activity payload.")

    counts: dict[str, int] = {}
    for event in payload:
        if not isinstance(event, dict):
            continue
        created_at = _parse_iso_datetime(event.get("created_at"))
        if not created_at:
            continue
        key = created_at.date().isoformat()
        counts[key] = counts.get(key, 0) + 1
    return _contributions_from_counts(counts, days, "gitlab_events")


async def fetch_code_provider_contributions(
    provider: str,
    access_token: str,
    base_url: str,
    api_base: str,
    username: str,
    user_id: str,
    auth_method: str,
    repositories: list[dict[str, Any]],
    days: int = CODE_PROVIDER_ACTIVITY_DAYS,
) -> dict[str, Any]:
    if provider == "github":
        return await fetch_github_contributions(
            base_url, access_token, username, auth_method, days
        )
    if provider == "gitlab":
        return await fetch_gitlab_contributions(
            access_token, api_base, user_id, auth_method, days
        )
    return _contributions_from_repositories(repositories, days)


async def fetch_code_provider_repositories(
    provider: str,
    access_token: str,
    base_url: str,
    api_base: str,
    username: str,
    user_id: str,
    auth_method: str = "token",
) -> dict[str, Any]:
    repos_url = _code_repos_url(provider, api_base, user_id)
    payload = await _fetch_json_value(
        repos_url,
        _provider_label(provider),
        headers=_code_provider_auth_headers(provider, access_token, auth_method),
    )
    if not isinstance(payload, list):
        raise ExternalApiError(
            f"{_provider_label(provider)}: returned an unexpected "
            "repositories payload."
        )

    repositories = [
        _summarize_repo(provider, repo) for repo in payload if isinstance(repo, dict)
    ]
    stats = _repository_stats(repositories)
    pinned_source = "unsupported"
    pinned_repositories: list[dict[str, Any]] = []
    if provider == "github":
        pinned_source = "github_pinned_items"
        try:
            github_pinned = await fetch_github_pinned_repositories(
                base_url, access_token, username, auth_method, repositories
            )
            if github_pinned:
                pinned_repositories = github_pinned
            else:
                pinned_source = "github_pinned_items_empty"
        except ExternalApiError:
            pinned_source = "github_pinned_items_unavailable"
    return {
        "repositories": repositories,
        "pinned_repositories": pinned_repositories,
        "repository_stats": stats,
        "repositories_synced_at": datetime.now(timezone.utc).isoformat(),
        "pinned_source": pinned_source,
    }


def _spotify_oauth_state_key(state: str) -> str:
    return f"integration:spotify_oauth:{state}"


def _spotify_oauth_callback_url(frontend_base_url: str) -> str:
    return f"{frontend_base_url}/api/integrations/spotify/oauth/callback"


def _spotify_result_url(
    frontend_base_url: str, success: bool, detail: Optional[str] = None
) -> str:
    query = {
        "tab": "integrations",
        "spotify": "connected" if success else "error",
    }
    if detail and not success:
        query["spotify_error"] = detail[:160]
    return f"{frontend_base_url}/dashboard?{urllib.parse.urlencode(query)}"


def _spotify_base_url(value: Any, fallback: str) -> str:
    return (_clean_text(value) or fallback).rstrip("/")


async def _get_spotify_urls(db: AsyncSession) -> tuple[str, str]:
    api_settings = await get_api_settings_data(db)
    return (
        _spotify_base_url(api_settings.get("spotify_api_base_url"), SPOTIFY_API_BASE),
        _spotify_base_url(
            api_settings.get("spotify_accounts_base_url"), SPOTIFY_ACCOUNTS_BASE
        ),
    )


def _spotify_url(
    api_base_url: str, path: str, params: Optional[dict[str, Any]] = None
) -> str:
    query = urllib.parse.urlencode(params or {})
    return f"{api_base_url.rstrip('/')}{path}{f'?{query}' if query else ''}"


def _spotify_basic_auth_header(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode("utf-8")
    return f"Basic {base64.b64encode(raw).decode('ascii')}"


def _spotify_auth_headers(access_token: str) -> dict[str, str]:
    return {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}


def _spotify_images_url(value: Any) -> Optional[str]:
    if not isinstance(value, list):
        return None
    for image in value:
        if isinstance(image, dict) and _clean_text(image.get("url")):
            return _clean_text(image.get("url"))
    return None


def _spotify_external_url(payload: dict[str, Any]) -> Optional[str]:
    urls = payload.get("external_urls")
    if isinstance(urls, dict):
        return _clean_text(urls.get("spotify"))
    return None


def _summarize_spotify_artist(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _clean_text(payload.get("id")),
        "name": _clean_text(payload.get("name")) or "Artist",
        "url": _spotify_external_url(payload),
        "image_url": _spotify_images_url(payload.get("images")),
        "genres": [
            str(genre)
            for genre in payload.get("genres", [])
            if isinstance(genre, str) and genre
        ][:8],
        "followers": (
            payload.get("followers", {}).get("total")
            if isinstance(payload.get("followers"), dict)
            else None
        ),
        "popularity": payload.get("popularity"),
    }


def _summarize_spotify_item(payload: dict[str, Any]) -> Optional[dict[str, Any]]:
    if not isinstance(payload, dict) or not _clean_text(payload.get("name")):
        return None

    item_type = _clean_text(payload.get("type")) or _clean_text(
        payload.get("currently_playing_type")
    )
    artists_payload = (
        payload.get("artists") if isinstance(payload.get("artists"), list) else []
    )
    artists = [
        _summarize_spotify_artist(artist)
        for artist in artists_payload
        if isinstance(artist, dict)
    ]
    album = payload.get("album") if isinstance(payload.get("album"), dict) else {}
    show = payload.get("show") if isinstance(payload.get("show"), dict) else {}
    image_url = _spotify_images_url(album.get("images")) or _spotify_images_url(
        payload.get("images")
    )
    if item_type == "episode" and not artists:
        publisher = _clean_text(show.get("publisher") or payload.get("publisher"))
        if publisher:
            artists = [{"id": None, "name": publisher, "url": None, "image_url": None}]

    return {
        "id": _clean_text(payload.get("id")),
        "type": item_type or "track",
        "name": _clean_text(payload.get("name")) or "Track",
        "artists": artists,
        "artist_names": ", ".join(
            artist["name"] for artist in artists if artist.get("name")
        ),
        "album_name": _clean_text(album.get("name") or show.get("name")),
        "image_url": image_url,
        "url": _spotify_external_url(payload),
        "duration_ms": _to_int(payload.get("duration_ms")),
        "explicit": bool(payload.get("explicit")),
        "preview_url": _clean_text(payload.get("preview_url")),
    }


def _empty_spotify_playback(checked_at: str) -> dict[str, Any]:
    return {
        "available": True,
        "is_active": False,
        "is_playing": False,
        "status": "idle",
        "status_label": "Ничего не слушает",
        "message": "Сейчас ничего не слушает",
        "track": None,
        "progress_ms": 0,
        "progress_percent": 0,
        "device": None,
        "checked_at": checked_at,
    }


def _summarize_spotify_current_playback(
    current_payload: Optional[dict[str, Any]],
    playback_payload: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    checked_at = datetime.now(timezone.utc).isoformat()
    source = current_payload or playback_payload
    if not isinstance(source, dict):
        return _empty_spotify_playback(checked_at)

    item = source.get("item") if isinstance(source.get("item"), dict) else {}
    track = _summarize_spotify_item(item) if item else None
    if not track:
        return _empty_spotify_playback(checked_at)

    progress_ms = _to_int(source.get("progress_ms"))
    duration_ms = _to_int(track.get("duration_ms"))
    progress_percent = (
        max(0, min(100, round((progress_ms / duration_ms) * 100)))
        if duration_ms > 0
        else 0
    )
    is_playing = bool(source.get("is_playing"))
    state = playback_payload if isinstance(playback_payload, dict) else {}
    device_payload = (
        state.get("device") if isinstance(state.get("device"), dict) else {}
    )
    device = None
    if device_payload:
        device = {
            "id": _clean_text(device_payload.get("id")),
            "name": _clean_text(device_payload.get("name")),
            "type": _clean_text(device_payload.get("type")),
            "is_active": bool(device_payload.get("is_active")),
            "volume_percent": device_payload.get("volume_percent"),
        }

    return {
        "available": True,
        "is_active": True,
        "is_playing": is_playing,
        "status": "playing" if is_playing else "paused",
        "status_label": "Слушает сейчас" if is_playing else "Пауза",
        "message": "Сейчас слушает" if is_playing else "Трек на паузе",
        "track": track,
        "progress_ms": progress_ms,
        "progress_percent": progress_percent,
        "device": device,
        "shuffle_state": state.get("shuffle_state"),
        "repeat_state": state.get("repeat_state"),
        "currently_playing_type": _clean_text(source.get("currently_playing_type")),
        "checked_at": checked_at,
    }


def _summarize_spotify_recent_item(payload: dict[str, Any]) -> Optional[dict[str, Any]]:
    track = payload.get("track") if isinstance(payload.get("track"), dict) else {}
    summary = _summarize_spotify_item(track)
    if not summary:
        return None
    summary["played_at"] = _clean_text(payload.get("played_at"))
    return summary


def _spotify_stats(
    recent_tracks: list[dict[str, Any]],
    top_tracks: list[dict[str, Any]],
    top_artists: list[dict[str, Any]],
) -> dict[str, Any]:
    recent_artists = {
        artist.get("name")
        for track in recent_tracks
        for artist in track.get("artists", [])
        if isinstance(artist, dict) and artist.get("name")
    }
    genre_counts: dict[str, int] = {}
    for artist in top_artists:
        for genre in artist.get("genres", []):
            if isinstance(genre, str) and genre:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
    top_genres = [
        {"genre": genre, "artists": count}
        for genre, count in sorted(
            genre_counts.items(), key=lambda item: (-item[1], item[0].lower())
        )[:6]
    ]
    return {
        "recent_tracks_count": len(recent_tracks),
        "unique_recent_artists": len(recent_artists),
        "top_tracks_count": len(top_tracks),
        "top_artists_count": len(top_artists),
        "top_genres": top_genres,
        "last_played_at": recent_tracks[0].get("played_at") if recent_tracks else None,
    }


async def _get_spotify_oauth_config(db: AsyncSession) -> tuple[str, str, str, str]:
    api_settings = await get_api_settings_data(db)
    client_id = _clean_text(api_settings.get("spotify_oauth_client_id"))
    client_secret = _clean_text(api_settings.get("spotify_oauth_client_secret"))
    if not client_id or not client_secret:
        raise ExternalApiError("Spotify OAuth app is not configured.", 400)
    return (
        client_id,
        client_secret,
        _spotify_base_url(api_settings.get("spotify_api_base_url"), SPOTIFY_API_BASE),
        _spotify_base_url(
            api_settings.get("spotify_accounts_base_url"), SPOTIFY_ACCOUNTS_BASE
        ),
    )


async def create_spotify_oauth_url(db: AsyncSession, user_id: UUID) -> str:
    client_id, _, _, accounts_base_url = await _get_spotify_oauth_config(db)
    frontend_base_url = await get_public_frontend_base_url(db)
    redirect_uri = _spotify_oauth_callback_url(frontend_base_url)
    state = secrets.token_urlsafe(32)

    redis = await get_redis()
    await redis.setex(
        _spotify_oauth_state_key(state),
        SPOTIFY_OAUTH_STATE_TTL_SECONDS,
        json.dumps({"user_id": str(user_id), "redirect_uri": redirect_uri}),
    )

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": SPOTIFY_SCOPES,
    }
    return f"{accounts_base_url}/authorize?{urllib.parse.urlencode(params)}"


async def _consume_spotify_oauth_state(state: str) -> Optional[dict[str, str]]:
    redis = await get_redis()
    key = _spotify_oauth_state_key(state)
    raw = await redis.get(key)
    if not raw:
        return None
    await redis.delete(key)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(str(raw))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


async def fetch_spotify_profile(
    access_token: str, api_base_url: str = SPOTIFY_API_BASE
) -> dict[str, Any]:
    payload = await _fetch_json(
        _spotify_url(api_base_url, "/me"),
        "Spotify",
        headers=_spotify_auth_headers(access_token),
    )
    images = payload.get("images") if isinstance(payload.get("images"), list) else []
    followers = (
        payload.get("followers") if isinstance(payload.get("followers"), dict) else {}
    )
    uid = _clean_text(payload.get("id"))
    return {
        "available": True,
        "provider": "spotify",
        "uid": uid or "",
        "display_name": _clean_text(payload.get("display_name")) or uid,
        "profile_url": _spotify_external_url(payload),
        "avatar_url": _spotify_images_url(images),
        "followers": followers.get("total"),
    }


async def fetch_spotify_current_playback(
    access_token: str, api_base_url: str = SPOTIFY_API_BASE
) -> dict[str, Any]:
    headers = _spotify_auth_headers(access_token)
    current_result, playback_result = await asyncio.gather(
        _fetch_optional_json(
            _spotify_url(
                api_base_url,
                "/me/player/currently-playing",
                {"additional_types": "track,episode"},
            ),
            "Spotify",
            headers=headers,
        ),
        _fetch_optional_json(
            _spotify_url(
                api_base_url, "/me/player", {"additional_types": "track,episode"}
            ),
            "Spotify",
            headers=headers,
        ),
        return_exceptions=True,
    )
    if isinstance(current_result, ExternalApiError):
        raise current_result
    if isinstance(current_result, Exception):
        raise ExternalApiError("Spotify: playback request failed.") from current_result
    playback_payload = (
        None if isinstance(playback_result, Exception) else playback_result
    )
    return _summarize_spotify_current_playback(current_result, playback_payload)


async def fetch_spotify_recent_tracks(
    access_token: str, limit: int = 10, api_base_url: str = SPOTIFY_API_BASE
) -> list[dict[str, Any]]:
    payload = await _fetch_json(
        _spotify_url(
            api_base_url,
            "/me/player/recently-played",
            {"limit": max(1, min(limit, 50))},
        ),
        "Spotify",
        headers=_spotify_auth_headers(access_token),
    )
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        summary = _summarize_spotify_recent_item(item)
        if summary:
            result.append(summary)
    return result


async def fetch_spotify_top_tracks(
    access_token: str,
    limit: int = 5,
    time_range: str = "short_term",
    api_base_url: str = SPOTIFY_API_BASE,
) -> list[dict[str, Any]]:
    payload = await _fetch_json(
        _spotify_url(
            api_base_url,
            "/me/top/tracks",
            {"limit": max(1, min(limit, 50)), "time_range": time_range},
        ),
        "Spotify",
        headers=_spotify_auth_headers(access_token),
    )
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    return [
        summary
        for item in items
        if isinstance(item, dict)
        for summary in [_summarize_spotify_item(item)]
        if summary
    ]


async def fetch_spotify_top_artists(
    access_token: str,
    limit: int = 5,
    time_range: str = "short_term",
    api_base_url: str = SPOTIFY_API_BASE,
) -> list[dict[str, Any]]:
    payload = await _fetch_json(
        _spotify_url(
            api_base_url,
            "/me/top/artists",
            {"limit": max(1, min(limit, 50)), "time_range": time_range},
        ),
        "Spotify",
        headers=_spotify_auth_headers(access_token),
    )
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    return [_summarize_spotify_artist(item) for item in items if isinstance(item, dict)]


async def build_spotify_metadata(
    access_token: str,
    api_base_url: str = SPOTIFY_API_BASE,
) -> tuple[dict[str, Any], Optional[str]]:
    now = datetime.now(timezone.utc).isoformat()
    metadata: dict[str, Any] = {
        "available": True,
        "provider": "spotify",
        "synced_at": now,
        "spotify_profile": None,
        "playback": _empty_spotify_playback(now),
        "recent_tracks": [],
        "top_tracks": [],
        "top_artists": [],
        "stats": {},
        "errors": [],
    }
    sync_errors: list[str] = []

    try:
        metadata["spotify_profile"] = await fetch_spotify_profile(
            access_token, api_base_url
        )
    except ExternalApiError as exc:
        sync_errors.append(str(exc))

    try:
        metadata["playback"] = await fetch_spotify_current_playback(
            access_token, api_base_url
        )
    except ExternalApiError as exc:
        sync_errors.append(str(exc))

    try:
        metadata["recent_tracks"] = await fetch_spotify_recent_tracks(
            access_token, api_base_url=api_base_url
        )
    except ExternalApiError as exc:
        sync_errors.append(str(exc))

    try:
        metadata["top_tracks"] = await fetch_spotify_top_tracks(
            access_token, api_base_url=api_base_url
        )
    except ExternalApiError as exc:
        sync_errors.append(str(exc))

    try:
        metadata["top_artists"] = await fetch_spotify_top_artists(
            access_token, api_base_url=api_base_url
        )
    except ExternalApiError as exc:
        sync_errors.append(str(exc))

    metadata["stats"] = _spotify_stats(
        [
            track
            for track in metadata.get("recent_tracks", [])
            if isinstance(track, dict)
        ],
        [track for track in metadata.get("top_tracks", []) if isinstance(track, dict)],
        [
            artist
            for artist in metadata.get("top_artists", [])
            if isinstance(artist, dict)
        ],
    )
    metadata["errors"] = sync_errors
    return metadata, "; ".join(sync_errors) or None


def _is_token_fresh(expires_at: Optional[datetime]) -> bool:
    if not expires_at:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > datetime.now(timezone.utc) + timedelta(seconds=60)


async def ensure_spotify_access_token(
    db: AsyncSession, account: ConnectedAccount
) -> str:
    access_token = _clean_text(account.access_token)
    if access_token and _is_token_fresh(account.token_expires_at):
        return access_token
    refresh_token = _clean_text(account.refresh_token)
    if not refresh_token:
        raise ExternalApiError("Spotify refresh token is missing.", 400)

    client_id, client_secret, _, accounts_base_url = await _get_spotify_oauth_config(db)
    token_payload = await _post_json(
        f"{accounts_base_url}/api/token",
        {"grant_type": "refresh_token", "refresh_token": refresh_token},
        "Spotify OAuth",
        headers={"Authorization": _spotify_basic_auth_header(client_id, client_secret)},
    )
    next_access_token = _clean_text(token_payload.get("access_token"))
    if not next_access_token:
        raise ExternalApiError("Spotify OAuth did not return an access token.", 400)

    account.access_token = next_access_token
    account.refresh_token = (
        _clean_text(token_payload.get("refresh_token")) or refresh_token
    )
    account.token_expires_at = _token_expires_at(token_payload.get("expires_in"))
    scopes = [
        scope
        for scope in str(token_payload.get("scope") or "").split()
        if scope.strip()
    ]
    if scopes:
        account.scopes = scopes
    account.updated_at = datetime.now(timezone.utc)
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return next_access_token


async def sync_spotify_account(db: AsyncSession, user_id: UUID) -> ConnectedAccount:
    account = await get_connected_account(db, user_id, "spotify")
    if not account:
        raise ExternalApiError("Spotify account is not connected.", 404)

    access_token = await ensure_spotify_access_token(db, account)
    api_base_url, _ = await _get_spotify_urls(db)
    metadata, sync_error = await build_spotify_metadata(access_token, api_base_url)
    profile = (
        metadata.get("spotify_profile")
        if isinstance(metadata.get("spotify_profile"), dict)
        else {}
    )
    provider_uid = _clean_text(profile.get("uid")) or account.provider_uid
    display_name = _clean_text(profile.get("display_name")) or account.display_name

    account = await upsert_single_provider_account(
        db,
        user_id,
        "spotify",
        provider_uid,
        display_name,
        metadata,
        sync_error,
        access_token=account.access_token,
        refresh_token=account.refresh_token,
        token_expires_at=account.token_expires_at,
        scopes=list(account.scopes or []),
    )
    await db.commit()
    await db.refresh(account)
    return account


async def connect_spotify_oauth_response(
    db: AsyncSession, query: dict[str, str]
) -> str:
    frontend_base_url = await get_public_frontend_base_url(db)
    state = _clean_text(query.get("state"))
    code = _clean_text(query.get("code"))
    if not state or not code:
        return _spotify_result_url(
            frontend_base_url, False, "Missing Spotify OAuth callback data."
        )

    state_data = await _consume_spotify_oauth_state(state)
    if not state_data:
        return _spotify_result_url(
            frontend_base_url, False, "Spotify sign-in expired. Try again."
        )

    user_id_raw = str(state_data.get("user_id") or "")
    redirect_uri = str(state_data.get("redirect_uri") or "")
    try:
        user_id = UUID(user_id_raw)
    except ValueError:
        return _spotify_result_url(frontend_base_url, False, "OAuth state is invalid.")

    try:
        (
            client_id,
            client_secret,
            api_base_url,
            accounts_base_url,
        ) = await _get_spotify_oauth_config(db)
        token_payload = await _post_json(
            f"{accounts_base_url}/api/token",
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            "Spotify OAuth",
            headers={
                "Authorization": _spotify_basic_auth_header(client_id, client_secret)
            },
        )
        access_token = _clean_text(token_payload.get("access_token"))
        refresh_token = _clean_text(token_payload.get("refresh_token"))
        if not access_token or not refresh_token:
            raise ExternalApiError(
                "Spotify OAuth did not return access and refresh tokens.", 400
            )
        metadata, sync_error = await build_spotify_metadata(access_token, api_base_url)
        profile = (
            metadata.get("spotify_profile")
            if isinstance(metadata.get("spotify_profile"), dict)
            else {}
        )
        provider_uid = _clean_text(profile.get("uid"))
        if not provider_uid:
            raise ExternalApiError("Spotify profile did not include a user id.", 400)
        scopes = [
            scope
            for scope in str(token_payload.get("scope") or SPOTIFY_SCOPES).split()
            if scope.strip()
        ]
        account = await upsert_single_provider_account(
            db,
            user_id,
            "spotify",
            provider_uid,
            _clean_text(profile.get("display_name")) or provider_uid,
            metadata,
            sync_error,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=_token_expires_at(token_payload.get("expires_in")),
            scopes=scopes,
        )
        await db.commit()
        await db.refresh(account)
    except ExternalApiError as exc:
        return _spotify_result_url(frontend_base_url, False, str(exc))

    return _spotify_result_url(frontend_base_url, True)


async def spotify_realtime_response(
    db: AsyncSession, account: ConnectedAccount
) -> dict[str, Any]:
    metadata = (
        dict(account.account_metadata)
        if isinstance(account.account_metadata, dict)
        else {}
    )
    try:
        access_token = await ensure_spotify_access_token(db, account)
        api_base_url, _ = await _get_spotify_urls(db)
        playback = await fetch_spotify_current_playback(access_token, api_base_url)
        sync_error = None
    except ExternalApiError as exc:
        playback = metadata.get("playback") or _empty_spotify_playback(
            datetime.now(timezone.utc).isoformat()
        )
        playback["available"] = False
        playback["message"] = str(exc)
        sync_error = str(exc)

    return {
        "available": sync_error is None,
        "provider": "spotify",
        "provider_uid": account.provider_uid,
        "display_name": account.display_name,
        "playback": playback,
        "recent_tracks": metadata.get("recent_tracks") or [],
        "top_tracks": metadata.get("top_tracks") or [],
        "top_artists": metadata.get("top_artists") or [],
        "stats": metadata.get("stats") or {},
        "last_synced_at": (
            account.last_synced_at.isoformat() if account.last_synced_at else None
        ),
        "sync_error": sync_error or account.sync_error,
    }


async def disconnect_spotify_account(db: AsyncSession, user_id: UUID) -> None:
    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user_id,
            ConnectedAccount.provider == "spotify",
        )
    )
    for account in result.scalars().all():
        await db.delete(account)
    await db.commit()


async def create_steam_openid_auth_url(db: AsyncSession, user_id: UUID) -> str:
    frontend_base_url = await get_public_frontend_base_url(db)
    state = secrets.token_urlsafe(32)
    redis = await get_redis()
    await redis.setex(
        _steam_openid_state_key(state), STEAM_OPENID_STATE_TTL_SECONDS, str(user_id)
    )

    return_to = _steam_openid_callback_url(frontend_base_url, state)
    realm = frontend_base_url
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
    frontend_base_url = await get_public_frontend_base_url(db)
    state = _clean_text(query.get("state"))
    if not state:
        return _steam_openid_result_url(
            frontend_base_url, False, "Missing Steam sign-in state."
        )

    user_id = await consume_steam_openid_state(state)
    if not user_id:
        return _steam_openid_result_url(
            frontend_base_url, False, "Steam sign-in expired. Try again."
        )

    try:
        steam_id = await verify_steam_openid_response(query)
        await connect_steam_account(db, user_id, steam_id)
    except ExternalApiError as exc:
        return _steam_openid_result_url(frontend_base_url, False, str(exc))

    return _steam_openid_result_url(frontend_base_url, True)


async def _get_code_oauth_config(db: AsyncSession, provider: str) -> tuple[str, str]:
    api_settings = await get_api_settings_data(db)
    client_id = _clean_text(api_settings.get(f"{provider}_oauth_client_id"))
    client_secret = _clean_text(api_settings.get(f"{provider}_oauth_client_secret"))
    if not client_id or not client_secret:
        raise ExternalApiError(
            f"{_provider_label(provider)} OAuth app is not configured.", 400
        )
    return client_id, client_secret


async def create_code_provider_oauth_url(
    db: AsyncSession,
    user_id: UUID,
    provider: str,
    raw_base_url: Optional[str] = None,
) -> str:
    provider = _normalize_code_provider(provider)
    base_url = _normalize_base_url(provider, raw_base_url)
    if not _is_default_code_provider_base_url(provider, base_url):
        raise ExternalApiError(
            "OAuth is not supported for self-hosted Git providers. Use an access token.",
            400,
        )
    client_id, _ = await _get_code_oauth_config(db, provider)
    frontend_base_url = await get_public_frontend_base_url(db)
    redirect_uri = _code_oauth_callback_url(frontend_base_url)
    state = secrets.token_urlsafe(32)
    urls = _code_provider_urls(provider, base_url)

    redis = await get_redis()
    await redis.setex(
        _code_oauth_state_key(state),
        CODE_OAUTH_STATE_TTL_SECONDS,
        json.dumps(
            {
                "user_id": str(user_id),
                "provider": provider,
                "base_url": base_url,
                "redirect_uri": redirect_uri,
            }
        ),
    )

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
        "scope": CODE_PROVIDER_SCOPES[provider],
    }
    return f"{urls['authorize']}?{urllib.parse.urlencode(params)}"


async def _consume_code_oauth_state(state: str) -> Optional[dict[str, str]]:
    redis = await get_redis()
    key = _code_oauth_state_key(state)
    raw = await redis.get(key)
    if not raw:
        return None
    await redis.delete(key)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(str(raw))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


async def fetch_code_provider_profile(
    provider: str,
    access_token: str,
    raw_base_url: Optional[str] = None,
    auth_method: str = "token",
) -> dict[str, Any]:
    provider = _normalize_code_provider(provider)
    base_url = _normalize_base_url(provider, raw_base_url)
    urls = _code_provider_urls(provider, base_url)
    effective_auth_method = auth_method
    try:
        payload = await _fetch_json(
            f"{urls['api']}/user",
            _provider_label(provider),
            headers=_code_provider_auth_headers(
                provider, access_token, effective_auth_method
            ),
        )
    except ExternalApiError as exc:
        alternate_auth_method = _alternate_code_provider_auth_method(
            provider, effective_auth_method
        )
        if not alternate_auth_method or not _looks_like_auth_rejection(exc):
            raise
        payload = await _fetch_json(
            f"{urls['api']}/user",
            _provider_label(provider),
            headers=_code_provider_auth_headers(
                provider, access_token, alternate_auth_method
            ),
        )
        effective_auth_method = alternate_auth_method

    metadata = _summarize_code_provider_user(provider, base_url, urls["api"], payload)
    metadata["auth_method"] = effective_auth_method
    try:
        repository_metadata = await fetch_code_provider_repositories(
            provider,
            access_token,
            base_url,
            urls["api"],
            str(metadata.get("username") or ""),
            str(metadata.get("uid") or ""),
            auth_method=effective_auth_method,
        )
        metadata.update(repository_metadata)
        metadata["repository_sync_error"] = None
    except ExternalApiError as exc:
        metadata["repositories"] = []
        metadata["pinned_repositories"] = []
        metadata["repository_stats"] = {}
        metadata["repository_sync_error"] = str(exc)
    repositories = [
        repo for repo in metadata.get("repositories", []) if isinstance(repo, dict)
    ]
    try:
        metadata["contributions"] = await fetch_code_provider_contributions(
            provider,
            access_token,
            base_url,
            urls["api"],
            str(metadata.get("username") or ""),
            str(metadata.get("uid") or ""),
            effective_auth_method,
            repositories,
            CODE_PROVIDER_ACTIVITY_DAYS,
        )
        metadata["activity_sync_error"] = None
    except ExternalApiError as exc:
        metadata["contributions"] = _contributions_from_repositories(
            repositories, CODE_PROVIDER_ACTIVITY_DAYS
        )
        metadata["activity_sync_error"] = str(exc)
    return metadata


async def connect_code_provider_token(
    db: AsyncSession,
    user_id: UUID,
    provider: str,
    access_token: str,
    raw_base_url: Optional[str] = None,
) -> ConnectedAccount:
    provider = _normalize_code_provider(provider)
    api_settings = await get_api_settings_data(db)
    if not bool(api_settings.get("code_provider_token_auth_enabled", True)):
        raise ExternalApiError("Token auth is disabled for Git providers.", 400)

    access_token = _clean_text(access_token) or ""
    if not access_token:
        raise ExternalApiError("Access token is required.", 400)

    metadata = await fetch_code_provider_profile(
        provider, access_token, raw_base_url, auth_method="token"
    )
    metadata["auth_method"] = str(metadata.get("auth_method") or "token")
    metadata["scopes"] = []

    account = await upsert_single_provider_account(
        db,
        user_id,
        provider,
        metadata["uid"],
        _clean_text(metadata.get("display_name")) or metadata["uid"],
        metadata,
        None,
        access_token=access_token,
        refresh_token=None,
        scopes=[],
    )
    account.refresh_token = None
    account.token_expires_at = None
    account.scopes = []
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def connect_code_provider_oauth_response(
    db: AsyncSession, query: dict[str, str]
) -> str:
    frontend_base_url = await get_public_frontend_base_url(db)
    state = _clean_text(query.get("state"))
    code = _clean_text(query.get("code"))
    if not state or not code:
        return _code_provider_result_url(
            frontend_base_url, "code", False, "Missing OAuth callback data."
        )

    state_data = await _consume_code_oauth_state(state)
    if not state_data:
        return _code_provider_result_url(
            frontend_base_url, "code", False, "OAuth sign-in expired. Try again."
        )

    provider = _normalize_code_provider(str(state_data.get("provider") or ""))
    base_url = _normalize_base_url(provider, state_data.get("base_url"))
    user_id_raw = str(state_data.get("user_id") or "")
    redirect_uri = str(state_data.get("redirect_uri") or "")

    try:
        user_id = UUID(user_id_raw)
    except ValueError:
        return _code_provider_result_url(
            frontend_base_url, provider, False, "OAuth state is invalid."
        )

    try:
        client_id, client_secret = await _get_code_oauth_config(db, provider)
        urls = _code_provider_urls(provider, base_url)
        token_payload = await _post_json(
            urls["token"],
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
            f"{_provider_label(provider)} OAuth",
        )
        access_token = _clean_text(token_payload.get("access_token"))
        if not access_token:
            raise ExternalApiError(
                f"{_provider_label(provider)} OAuth did not return an access token.",
                400,
            )
        metadata = await fetch_code_provider_profile(
            provider, access_token, base_url, auth_method="oauth"
        )
        metadata["auth_method"] = "oauth"
        metadata["scopes"] = [
            scope
            for scope in str(token_payload.get("scope") or "").split()
            if scope.strip()
        ]
        refresh_token = _clean_text(token_payload.get("refresh_token"))
        expires_at = _token_expires_at(token_payload.get("expires_in"))
        account = await upsert_single_provider_account(
            db,
            user_id,
            provider,
            metadata["uid"],
            _clean_text(metadata.get("display_name")) or metadata["uid"],
            metadata,
            None,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=expires_at,
            scopes=metadata["scopes"],
        )
        account.refresh_token = refresh_token
        account.token_expires_at = expires_at
        db.add(account)
        await db.commit()
        await db.refresh(account)
    except ExternalApiError as exc:
        return _code_provider_result_url(frontend_base_url, provider, False, str(exc))

    return _code_provider_result_url(frontend_base_url, provider, True)


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
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    token_expires_at: Optional[datetime] = None,
    scopes: Optional[list[str]] = None,
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
    if access_token is not None:
        account.access_token = access_token
    if refresh_token is not None:
        account.refresh_token = refresh_token
    if token_expires_at is not None:
        account.token_expires_at = token_expires_at
    if scopes is not None:
        account.scopes = scopes
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


async def sync_code_provider_account(
    db: AsyncSession, user_id: UUID, provider: str
) -> ConnectedAccount:
    provider = _normalize_code_provider(provider)
    account = await get_connected_account(db, user_id, provider)
    if not account or not account.access_token:
        raise ExternalApiError(
            f"{_provider_label(provider)} account is not connected.", 404
        )

    metadata = (
        dict(account.account_metadata)
        if isinstance(account.account_metadata, dict)
        else {}
    )
    auth_method = str(metadata.get("auth_method") or "token")
    base_url = _clean_text(metadata.get("base_url"))
    next_metadata = await fetch_code_provider_profile(
        provider, account.access_token, base_url, auth_method=auth_method
    )
    next_metadata["auth_method"] = str(next_metadata.get("auth_method") or auth_method)
    next_metadata["scopes"] = list(account.scopes or [])

    account = await upsert_single_provider_account(
        db,
        user_id,
        provider,
        next_metadata["uid"],
        _clean_text(next_metadata.get("display_name")) or next_metadata["uid"],
        next_metadata,
        None,
        access_token=account.access_token,
        refresh_token=account.refresh_token,
        token_expires_at=account.token_expires_at,
        scopes=list(account.scopes or []),
    )
    await db.commit()
    await db.refresh(account)
    return account


async def disconnect_code_provider_account(
    db: AsyncSession, user_id: UUID, provider: str
) -> None:
    provider = _normalize_code_provider(provider)
    result = await db.execute(
        select(ConnectedAccount).where(
            ConnectedAccount.user_id == user_id,
            ConnectedAccount.provider == provider,
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
            github_oauth_ready=bool(
                _clean_text(api_settings.get("github_oauth_client_id"))
                and _clean_text(api_settings.get("github_oauth_client_secret"))
            ),
            gitlab_oauth_ready=bool(
                _clean_text(api_settings.get("gitlab_oauth_client_id"))
                and _clean_text(api_settings.get("gitlab_oauth_client_secret"))
            ),
            gitea_oauth_ready=bool(
                _clean_text(api_settings.get("gitea_oauth_client_id"))
                and _clean_text(api_settings.get("gitea_oauth_client_secret"))
            ),
            spotify_oauth_ready=bool(
                _clean_text(api_settings.get("spotify_oauth_client_id"))
                and _clean_text(api_settings.get("spotify_oauth_client_secret"))
            ),
            code_provider_token_auth_enabled=bool(
                api_settings.get("code_provider_token_auth_enabled", True)
            ),
        ),
    )
