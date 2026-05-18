import asyncio
import logging
import secrets
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import or_, select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.integration import ConnectedAccount
from app.redis import get_redis
from app.services.external_integrations import ExternalApiError, connect_steam_account

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SteamSyncCandidate:
    account_id: UUID
    user_id: UUID
    provider_uid: str


class SteamAutoSyncScheduler:
    def __init__(self) -> None:
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if not settings.STEAM_AUTO_SYNC_ENABLED:
            logger.info("Automatic Steam sync is disabled.")
            return
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._run(), name="steam-auto-sync")

    async def stop(self) -> None:
        if not self._task:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def _run(self) -> None:
        startup_delay = max(0, settings.STEAM_AUTO_SYNC_STARTUP_DELAY_SECONDS)
        if startup_delay:
            await asyncio.sleep(startup_delay)

        poll_seconds = max(30, settings.STEAM_AUTO_SYNC_POLL_SECONDS)
        while True:
            try:
                await sync_due_steam_accounts()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Automatic Steam sync cycle failed.")
            await asyncio.sleep(poll_seconds)


async def sync_due_steam_accounts() -> int:
    interval_seconds = max(60, settings.STEAM_AUTO_SYNC_INTERVAL_SECONDS)
    batch_size = max(1, settings.STEAM_AUTO_SYNC_BATCH_SIZE)
    stale_before = datetime.now(timezone.utc) - timedelta(seconds=interval_seconds)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                ConnectedAccount.id,
                ConnectedAccount.user_id,
                ConnectedAccount.provider_uid,
            )
            .where(
                ConnectedAccount.provider == "steam",
                ConnectedAccount.is_active.is_(True),
                or_(
                    ConnectedAccount.last_synced_at.is_(None),
                    ConnectedAccount.last_synced_at <= stale_before,
                ),
            )
            .order_by(ConnectedAccount.last_synced_at.asc().nullsfirst())
            .limit(batch_size)
        )
        candidates = [
            SteamSyncCandidate(
                account_id=row.id,
                user_id=row.user_id,
                provider_uid=row.provider_uid,
            )
            for row in result.all()
        ]

    synced_count = 0
    for candidate in candidates:
        if await _sync_steam_candidate(candidate):
            synced_count += 1
    return synced_count


async def _sync_steam_candidate(candidate: SteamSyncCandidate) -> bool:
    lock_key = _steam_sync_lock_key(candidate.account_id)
    lock_token = await _acquire_lock(lock_key)
    if not lock_token:
        return False

    try:
        async with AsyncSessionLocal() as db:
            try:
                account = await db.get(ConnectedAccount, candidate.account_id)
                if (
                    not account
                    or account.provider != "steam"
                    or not account.is_active
                    or account.provider_uid != candidate.provider_uid
                    or not _is_due_for_auto_sync(account.last_synced_at)
                ):
                    return False
                await connect_steam_account(
                    db, candidate.user_id, candidate.provider_uid
                )
            except Exception:
                await db.rollback()
                raise
        logger.info("Automatically synced Steam account %s.", candidate.account_id)
        return True
    except ExternalApiError as exc:
        logger.warning(
            "Automatic Steam sync failed for account %s: %s",
            candidate.account_id,
            exc,
        )
        await _mark_sync_failure(candidate.account_id, str(exc))
        return False
    except Exception:
        logger.exception(
            "Unexpected automatic Steam sync failure for account %s.",
            candidate.account_id,
        )
        await _mark_sync_failure(
            candidate.account_id, "Automatic Steam sync failed unexpectedly."
        )
        return False
    finally:
        await _release_lock(lock_key, lock_token)


def _steam_sync_lock_key(account_id: UUID) -> str:
    return f"integration:steam:auto-sync:{account_id}"


def _is_due_for_auto_sync(last_synced_at: datetime | None) -> bool:
    if last_synced_at is None:
        return True
    if last_synced_at.tzinfo is None:
        last_synced_at = last_synced_at.replace(tzinfo=timezone.utc)
    interval_seconds = max(60, settings.STEAM_AUTO_SYNC_INTERVAL_SECONDS)
    stale_before = datetime.now(timezone.utc) - timedelta(seconds=interval_seconds)
    return last_synced_at <= stale_before


async def _acquire_lock(key: str) -> str | None:
    redis = await get_redis()
    token = secrets.token_urlsafe(16)
    lock_seconds = max(120, min(settings.STEAM_AUTO_SYNC_INTERVAL_SECONDS, 900))
    acquired = await redis.set(key, token, ex=lock_seconds, nx=True)
    return token if acquired else None


async def _release_lock(key: str, token: str) -> None:
    with suppress(Exception):
        redis = await get_redis()
        await redis.eval(
            "if redis.call('get', KEYS[1]) == ARGV[1] "
            "then return redis.call('del', KEYS[1]) else return 0 end",
            1,
            key,
            token,
        )


async def _mark_sync_failure(account_id: UUID, message: str) -> None:
    async with AsyncSessionLocal() as db:
        account = await db.get(ConnectedAccount, account_id)
        if not account:
            return

        now = datetime.now(timezone.utc)
        account.sync_error = message[:500]
        account.last_synced_at = now
        account.updated_at = now
        db.add(account)
        await db.commit()
