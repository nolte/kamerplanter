"""Redis-backed OAuth state store with TTL for CSRF protection."""

import json

import redis
import structlog

logger = structlog.get_logger()

_PREFIX = "kp:oauth:state:"


class RedisOAuthStateStore:
    """Store and retrieve OAuth state parameters in Redis with automatic expiry."""

    def __init__(self, redis_url: str) -> None:
        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)

    def save_state(self, state: str, data: dict, ttl: int = 300) -> None:
        """Store OAuth state data with a TTL (default 5 minutes)."""
        self._redis.set(f"{_PREFIX}{state}", json.dumps(data), ex=ttl)
        logger.debug("oauth_state_saved", state=state[:8])

    def get_and_delete(self, state: str) -> dict | None:
        """Retrieve and atomically delete OAuth state (one-time use)."""
        key = f"{_PREFIX}{state}"
        pipe = self._redis.pipeline()
        pipe.get(key)
        pipe.delete(key)
        results = pipe.execute()
        raw = results[0]
        if raw is None:
            logger.warning("oauth_state_not_found", state=state[:8])
            return None
        return json.loads(raw)
