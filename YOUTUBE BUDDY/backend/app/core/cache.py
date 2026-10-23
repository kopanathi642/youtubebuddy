import json
import time
from typing import Any, Optional

from app.core.config import settings

try:
    from redis.asyncio import Redis
    redis_available = True
except ImportError:
    Redis = None  # type: ignore[assignment]
    redis_available = False

redis_client: Optional[Redis] = None
_memory_cache: dict[str, tuple[float, str]] = {}


async def init_cache() -> None:
    global redis_client
    if not redis_available or not settings.REDIS_URL:
        redis_client = None
        return

    try:
        client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        await client.ping()
        redis_client = client
    except Exception:
        if "client" in locals():
            await client.close()
        redis_client = None


async def close_cache() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()
    _memory_cache.clear()


async def get_cache(key: str) -> Optional[Any]:
    if redis_client:
        try:
            data = await redis_client.get(key)
            return json.loads(data) if data else None
        except Exception:
            pass

    # Fast in-memory TTL fallback
    item = _memory_cache.get(key)
    if not item:
        return None
    expires_at, payload_str = item
    if time.time() > expires_at:
        _memory_cache.pop(key, None)
        return None
    try:
        return json.loads(payload_str)
    except Exception:
        return None


async def set_cache(key: str, value: Any, expire: int = 300) -> None:
    try:
        data_str = json.dumps(value, default=str)
    except Exception:
        return

    if redis_client:
        try:
            await redis_client.setex(key, expire, data_str)
            return
        except Exception:
            pass

    # Fast in-memory TTL fallback
    _memory_cache[key] = (time.time() + expire, data_str)


async def delete_cache(key: str) -> None:
    if redis_client:
        try:
            await redis_client.delete(key)
        except Exception:
            pass
    _memory_cache.pop(key, None)

