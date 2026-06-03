from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.profile import (
    BlockCreate,
    BlockReorder,
    BlockResponse,
    BlockUpdate,
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)
from app.services import profile as svc

router = APIRouter(tags=["profiles"])


def _account_by_provider(profile, provider: str):
    user = profile.user if profile.user else None
    accounts = getattr(user, "connected_accounts", []) if user else []
    return next(
        (
            account
            for account in accounts
            if account.provider == provider and account.is_active
        ),
        None,
    )


def _account_metadata(account) -> dict:
    if not account or not isinstance(account.account_metadata, dict):
        return {}
    return account.account_metadata


def _display_name_from_metadata(account, metadata: dict, provider: str) -> str | None:
    if account and account.display_name:
        return account.display_name
    if provider == "steam":
        steam_profile = metadata.get("steam_profile")
        if isinstance(steam_profile, dict):
            return steam_profile.get("personaname")
    if provider == "faceit":
        return metadata.get("nickname") or metadata.get("game_player_name")
    if provider in {"github", "gitlab", "gitea"}:
        return metadata.get("display_name") or metadata.get("username")
    return None


def _git_repository_stats(repositories: list[dict]) -> dict:
    languages: dict[str, int] = {}
    for repo in repositories:
        language = repo.get("language")
        if isinstance(language, str) and language:
            languages[language] = languages.get(language, 0) + 1
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
        "stars": sum(int(repo.get("stars") or 0) for repo in repositories),
        "forks": sum(int(repo.get("forks") or 0) for repo in repositories),
        "top_languages": [
            {"language": language, "repositories": count}
            for language, count in sorted(
                languages.items(), key=lambda item: (-item[1], item[0].lower())
            )[:6]
        ],
        "last_activity_at": last_activity_at,
    }


def _git_contributions_days(value) -> int:
    try:
        days = int(value)
    except (TypeError, ValueError):
        days = 30
    return min(90, max(1, days))


def _slice_git_contributions(activity: dict | None, days: int) -> dict:
    days = _git_contributions_days(days)
    source_days = []
    if isinstance(activity, dict) and isinstance(activity.get("days"), list):
        source_days = [day for day in activity["days"] if isinstance(day, dict)]
    visible_days = source_days[-days:]
    total = sum(int(day.get("count") or 0) for day in visible_days)
    return {
        "days": visible_days,
        "total": total,
        "active_days": sum(1 for day in visible_days if int(day.get("count") or 0) > 0),
        "window_days": len(visible_days) or days,
        "from": visible_days[0].get("date") if visible_days else None,
        "to": visible_days[-1].get("date") if visible_days else None,
        "source": activity.get("source") if isinstance(activity, dict) else None,
    }


def _git_provider_label(provider: str) -> str:
    return {
        "github": "GitHub",
        "gitlab": "GitLab",
        "gitea": "Gitea",
    }.get(provider, provider)


def _sanitize_block_config(block_type: str, config: dict | None) -> dict:
    clean = dict(config or {})
    synced_keys = {
        "widget_steam": (
            "steam_id",
            "steam_display_name",
            "connected_account_id",
            "steam_profile",
            "steam_recent_games",
            "steam_profile_stats",
            "steam_inventory_highlight",
            "steam_sync_error",
            "steam_last_synced_at",
            "faceit_profile",
        ),
        "widget_faceit": (
            "nickname",
            "faceit_display_name",
            "connected_account_id",
            "faceit_profile",
            "faceit_sync_error",
            "faceit_last_synced_at",
        ),
        "widget_github": (
            "git_provider",
            "git_provider_label",
            "git_display_name",
            "git_profile",
            "git_repository_stats",
            "git_pinned_repositories",
            "git_repositories",
            "git_contributions",
            "git_activity_sync_error",
            "git_sync_error",
            "git_last_synced_at",
            "github_display_name",
            "connected_account_id",
            "github_profile",
            "github_sync_error",
            "github_last_synced_at",
        ),
    }
    for key in synced_keys.get(block_type, ()):
        clean.pop(key, None)
    return clean


def _enriched_block_config(profile, block) -> dict:
    config = dict(block.config or {})
    steam_account = _account_by_provider(profile, "steam")
    faceit_account = _account_by_provider(profile, "faceit")
    code_accounts = {
        provider: _account_by_provider(profile, provider)
        for provider in ("github", "gitlab", "gitea")
    }
    steam_metadata = _account_metadata(steam_account)
    faceit_metadata = _account_metadata(faceit_account)

    if block.block_type == "widget_steam":
        if steam_account:
            config["steam_id"] = steam_account.provider_uid
            config["steam_display_name"] = (
                _display_name_from_metadata(steam_account, steam_metadata, "steam")
                or steam_account.provider_uid
            )
            config["connected_account_id"] = str(steam_account.id)
            config["steam_profile"] = steam_metadata.get("steam_profile")
            config["steam_recent_games"] = steam_metadata.get("recent_games") or []
            config["steam_profile_stats"] = steam_metadata.get("profile_stats") or {}
            config["steam_inventory_highlight"] = steam_metadata.get(
                "inventory_highlight"
            )
            config["steam_sync_error"] = steam_account.sync_error
            config["steam_last_synced_at"] = (
                steam_account.last_synced_at.isoformat()
                if steam_account.last_synced_at
                else None
            )
            config["faceit_profile"] = faceit_metadata or steam_metadata.get(
                "faceit_profile"
            )
        else:
            for key in (
                "steam_id",
                "steam_display_name",
                "connected_account_id",
                "steam_profile",
                "steam_recent_games",
                "steam_profile_stats",
                "steam_inventory_highlight",
                "steam_sync_error",
                "steam_last_synced_at",
                "faceit_profile",
            ):
                config.pop(key, None)

    if block.block_type == "widget_faceit":
        if faceit_account:
            display_name = _display_name_from_metadata(
                faceit_account, faceit_metadata, "faceit"
            )
            config["nickname"] = display_name
            config["faceit_display_name"] = display_name
            config["connected_account_id"] = str(faceit_account.id)
            config["faceit_profile"] = faceit_metadata
            config["faceit_sync_error"] = faceit_account.sync_error
            config["faceit_last_synced_at"] = (
                faceit_account.last_synced_at.isoformat()
                if faceit_account.last_synced_at
                else None
            )
        else:
            for key in (
                "nickname",
                "faceit_display_name",
                "connected_account_id",
                "faceit_profile",
                "faceit_sync_error",
                "faceit_last_synced_at",
            ):
                config.pop(key, None)

    if block.block_type == "widget_github":
        requested_provider = str(
            config.get("provider") or config.get("git_provider") or "github"
        )
        if requested_provider not in code_accounts:
            requested_provider = "github"
        git_account = code_accounts.get(requested_provider)
        config["provider"] = requested_provider
        config["git_provider"] = requested_provider
        config["git_provider_label"] = _git_provider_label(requested_provider)
        if git_account:
            git_metadata = _account_metadata(git_account)
            provider = git_account.provider
            username = git_metadata.get("username")
            display_name = _display_name_from_metadata(
                git_account, git_metadata, provider
            )
            if username:
                config["username"] = username
            include_private = bool(config.get("include_private_repositories"))
            contribution_days = _git_contributions_days(
                config.get("contributions_days")
            )
            repositories = [
                repo
                for repo in (git_metadata.get("repositories") or [])
                if isinstance(repo, dict)
                and (include_private or not repo.get("is_private"))
            ]
            pinned_repositories = [
                repo
                for repo in (git_metadata.get("pinned_repositories") or [])
                if isinstance(repo, dict)
                and (include_private or not repo.get("is_private"))
            ]
            config["provider"] = provider
            config["git_provider"] = provider
            config["git_provider_label"] = _git_provider_label(provider)
            config["git_display_name"] = display_name
            config["git_profile"] = git_metadata
            config["git_repository_stats"] = _git_repository_stats(repositories)
            config["git_pinned_repositories"] = pinned_repositories
            config["git_repositories"] = repositories
            config["git_contributions"] = _slice_git_contributions(
                git_metadata.get("contributions"), contribution_days
            )
            config["git_activity_sync_error"] = git_metadata.get("activity_sync_error")
            config["git_sync_error"] = git_account.sync_error or git_metadata.get(
                "repository_sync_error"
            )
            config["git_last_synced_at"] = (
                git_account.last_synced_at.isoformat()
                if git_account.last_synced_at
                else None
            )
            config["github_display_name"] = display_name
            config["connected_account_id"] = str(git_account.id)
            config["github_profile"] = git_metadata
            config["github_sync_error"] = git_account.sync_error
            config["github_last_synced_at"] = (
                git_account.last_synced_at.isoformat()
                if git_account.last_synced_at
                else None
            )
        else:
            for key in (
                "git_display_name",
                "git_profile",
                "git_repository_stats",
                "git_pinned_repositories",
                "git_repositories",
                "git_contributions",
                "git_activity_sync_error",
                "git_sync_error",
                "git_last_synced_at",
                "github_display_name",
                "connected_account_id",
                "github_profile",
                "github_sync_error",
                "github_last_synced_at",
            ):
                config.pop(key, None)

    return config


def _block_to_response(profile, block) -> BlockResponse:
    return BlockResponse(
        id=block.id,
        block_type=block.block_type,
        sort_order=block.sort_order,
        is_visible=block.is_visible,
        config=_enriched_block_config(profile, block),
    )


def _to_response(profile) -> ProfileResponse:
    trans = next((t for t in profile.translations if t.locale == "ru"), None)
    return ProfileResponse(
        id=profile.id,
        slug=profile.slug,
        status=profile.status,
        display_name=trans.display_name if trans else "",
        bio=trans.bio if trans else None,
        tags=trans.tags if trans else [],
        blocks=[_block_to_response(profile, b) for b in profile.blocks],
        theme_preset=profile.theme_preset,
        theme_tokens=profile.theme_tokens or {},
        accent_color=profile.accent_color,
        avatar_url=profile.user.avatar_url if profile.user else None,
    )


# ── My profile ────────────────────────────────────────────────────────────────


@router.get("/profiles/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc.get_profile_by_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _to_response(profile)


@router.post("/profiles", response_model=ProfileResponse, status_code=201)
async def create_profile(
    body: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if await svc.get_profile_by_user(db, current_user.id):
        raise HTTPException(status_code=409, detail="Profile already exists")
    if await svc.slug_taken(db, body.slug):
        raise HTTPException(status_code=409, detail="Slug already taken")

    profile = await svc.create_profile(
        db,
        user_id=current_user.id,
        slug=body.slug,
        display_name=body.display_name,
        bio=body.bio,
        tags=body.tags,
    )
    return _to_response(profile)


@router.patch("/profiles/me", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc.get_profile_by_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if body.slug and body.slug != profile.slug:
        if await svc.slug_taken(db, body.slug, exclude_id=profile.id):
            raise HTTPException(status_code=409, detail="Slug already taken")

    profile = await svc.update_profile(
        db,
        profile,
        slug=body.slug,
        status=body.status,
        display_name=body.display_name,
        bio=body.bio,
        tags=body.tags,
        theme_preset=body.theme_preset,
        theme_tokens=body.theme_tokens,
        accent_color=body.accent_color,
    )
    return _to_response(profile)


# ── Blocks ────────────────────────────────────────────────────────────────────


@router.post("/profiles/me/blocks", response_model=BlockResponse, status_code=201)
async def create_block(
    body: BlockCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc.get_profile_by_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    block = await svc.create_block(
        db,
        profile.id,
        body.block_type,
        _sanitize_block_config(body.block_type, body.config),
    )
    return _block_to_response(profile, block)


@router.patch("/profiles/me/blocks/{block_id}", response_model=BlockResponse)
async def update_block(
    block_id: UUID,
    body: BlockUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc.get_profile_by_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    block = next((b for b in profile.blocks if b.id == block_id), None)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    next_config = (
        _sanitize_block_config(block.block_type, body.config)
        if body.config is not None
        else None
    )
    block = await svc.update_block(
        db, block, config=next_config, is_visible=body.is_visible
    )
    return _block_to_response(profile, block)


@router.delete("/profiles/me/blocks/{block_id}", status_code=204)
async def delete_block(
    block_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc.get_profile_by_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    block = next((b for b in profile.blocks if b.id == block_id), None)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    await svc.delete_block(db, block)


@router.put("/profiles/me/blocks/reorder", status_code=204)
async def reorder_blocks(
    body: BlockReorder,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc.get_profile_by_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    await svc.reorder_blocks(db, profile.id, body.ids)


# ── Public ────────────────────────────────────────────────────────────────────


@router.get("/u/{slug}", response_model=ProfileResponse)
async def public_profile(slug: str, db: AsyncSession = Depends(get_db)):
    profile = await svc.get_profile_by_slug(db, slug)
    if not profile or profile.status == "draft":
        raise HTTPException(status_code=404, detail="Profile not found")
    return _to_response(profile)
