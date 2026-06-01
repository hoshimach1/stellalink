import asyncio
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
    "gitlab": "read_user read_repository",
    "gitea": "read:user read:repository",
}


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
        "is_private": _repo_bool(repo, "private"),
        "is_fork": _repo_bool(repo, "fork"),
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


def _select_pinned_repositories(
    repositories: list[dict[str, Any]], limit: int = 6
) -> list[dict[str, Any]]:
    candidates = [repo for repo in repositories if not repo.get("is_archived")]
    if not candidates:
        candidates = repositories
    return sorted(
        candidates,
        key=lambda repo: (
            _to_int(repo.get("stars")),
            str(repo.get("updated_at") or ""),
            str(repo.get("name") or "").lower(),
        ),
        reverse=True,
    )[:limit]


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
    pinned_source = "selected_by_stars_and_activity"
    pinned_repositories = _select_pinned_repositories(repositories)
    if provider == "github":
        try:
            github_pinned = await fetch_github_pinned_repositories(
                base_url, access_token, username, auth_method, repositories
            )
            if github_pinned:
                pinned_repositories = github_pinned
                pinned_source = "github_pinned_items"
        except ExternalApiError:
            pinned_source = "selected_by_stars_and_activity"
    return {
        "repositories": repositories,
        "pinned_repositories": pinned_repositories,
        "repository_stats": stats,
        "repositories_synced_at": datetime.now(timezone.utc).isoformat(),
        "pinned_source": pinned_source,
    }


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
    payload = await _fetch_json(
        f"{urls['api']}/user",
        _provider_label(provider),
        headers=_code_provider_auth_headers(provider, access_token, auth_method),
    )
    metadata = _summarize_code_provider_user(provider, base_url, urls["api"], payload)
    try:
        metadata.update(
            await fetch_code_provider_repositories(
                provider,
                access_token,
                base_url,
                urls["api"],
                str(metadata.get("username") or ""),
                str(metadata.get("uid") or ""),
                auth_method=auth_method,
            )
        )
        metadata["repository_sync_error"] = None
    except ExternalApiError as exc:
        metadata["repositories"] = []
        metadata["pinned_repositories"] = []
        metadata["repository_stats"] = {}
        metadata["repository_sync_error"] = str(exc)
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
    metadata["auth_method"] = "token"
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
    next_metadata["auth_method"] = auth_method
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
            code_provider_token_auth_enabled=bool(
                api_settings.get("code_provider_token_auth_enabled", True)
            ),
        ),
    )
