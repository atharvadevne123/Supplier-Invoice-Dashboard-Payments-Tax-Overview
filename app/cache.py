"""In-memory caching utilities with TTL support for expensive aggregations."""

import hashlib
import logging
import time
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[Any, float]] = {}


def _make_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Build a stable, collision-resistant cache key from call arguments.

    Uses MD5 over the repr of (func_name, args, sorted_kwargs) for
    compactness; collisions are acceptable for a non-security cache.

    Args:
        func_name: Qualified name of the cached function.
        args: Positional arguments tuple.
        kwargs: Keyword arguments dict.

    Returns:
        Hex digest string used as the cache key.
    """
    raw = repr((func_name, args, sorted(kwargs.items())))
    return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()


def ttl_cache(ttl_seconds: int = 60) -> Callable:
    """Decorator that caches function return values for ttl_seconds.

    The cache key is a stable MD5 hash of the function name and all
    positional/keyword arguments. Uses module-level _cache dict to avoid
    threading complexity in single-process deploys.

    Args:
        ttl_seconds: Time-to-live in seconds before a cached entry expires.

    Returns:
        Decorator that wraps the target function with caching.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = _make_cache_key(func.__qualname__, args, kwargs)
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


def get_or_set(key: str, factory: "Callable[[], Any]", ttl_seconds: int = 60) -> Any:
    """Return a cached value by raw key, computing and caching it if missing or expired.

    Unlike the ``ttl_cache`` decorator, this function works with explicit string keys,
    making it suitable for dynamic cache operations such as per-request query results.

    Args:
        key: Unique string key identifying the cached value.
        factory: Zero-argument callable that computes the value on a cache miss.
        ttl_seconds: Time-to-live in seconds for the computed value.

    Returns:
        Cached value (or freshly computed value on a miss).
    """
    now = time.monotonic()
    if key in _cache:
        value, expires_at = _cache[key]
        if now < expires_at:
            logger.debug("Cache hit (raw key): %s", key)
            return value
    result = factory()
    _cache[key] = (result, now + ttl_seconds)
    logger.debug("Cache set (raw key): %s (ttl=%ds)", key, ttl_seconds)
    return result


def cache_stats() -> dict[str, int]:
    """Return basic cache statistics for the /metrics endpoint.

    Returns:
        Dict with total_entries and live_entries counts.
    """
    now = time.monotonic()
    live = sum(1 for _, (_, exp) in _cache.items() if exp > now)
    return {"total_entries": len(_cache), "live_entries": live}
