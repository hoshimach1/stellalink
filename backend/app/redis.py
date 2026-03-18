from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis, from_url

from app.config import settings

_redis: Redis | None = None


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


# --- Widget cache helpers ---

def _widget_key(account_id: str, data_type: str) -> str:
    return f"widget:{account_id}:{data_type}"


async def get_widget_cache(account_id: str, data_type: str) -> Any | None:
    r = await get_redis()
    raw = await r.get(_widget_key(account_id, data_type))
    return json.loads(raw) if raw else None


async def set_widget_cache(account_id: str, data_type: str, payload: Any, ttl_seconds: int = 300) -> None:
    r = await get_redis()
    await r.setex(_widget_key(account_id, data_type), ttl_seconds, json.dumps(payload))


async def invalidate_widget_cache(account_id: str, data_type: str) -> None:
    r = await get_redis()
    await r.delete(_widget_key(account_id, data_type))
