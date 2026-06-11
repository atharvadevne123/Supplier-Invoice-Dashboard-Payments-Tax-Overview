"""In-memory caching utilities with TTL support for expensive aggregations."""

import logging
import time
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[Any, float]] = {}


def ttl_cache(ttl_seconds: int = 60) -> Callable:
    """Decorator that caches function return values for ttl_seconds.

    The cache key is based on the function name and all positional/keyword args.
    Uses module-level _cache dict to avoid threading complexity in single-process deploys.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{func.__qualname__}:{args}:{sorted(kwargs.items())}"
            now = time.monotonic()
            if key in _cache:
                value, expires_at = _cache[key]
                if now < expires_at:
                    logger.debug("Cache hit: %s", func.__qualname__)
                    return value
                logger.debug("Cache expired: %s", func.__qualname__)
            result = func(*args, **kwargs)
            _cache[key] = (result, now + ttl_seconds)
            logger.debug("Cache set: %s (ttl=%ds)", func.__qualname__, ttl_seconds)
            return result
        return wrapper
    return decorator


def invalidate_all() -> None:
    """Clear all cached entries — call after writes that affect aggregations."""
    count = len(_cache)
    _cache.clear()
    logger.info("Cache invalidated: %d entries cleared", count)


def cache_stats() -> dict[str, int]:
    """Return basic cache statistics for the /metrics endpoint."""
    now = time.monotonic()
    live = sum(1 for _, (_, exp) in _cache.items() if exp > now)
    return {"total_entries": len(_cache), "live_entries": live}
