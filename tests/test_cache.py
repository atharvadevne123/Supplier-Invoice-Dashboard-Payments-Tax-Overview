"""Tests for the TTL cache module."""



from app.cache import cache_stats, invalidate_all, ttl_cache


def test_cache_stores_and_returns_value() -> None:
    call_count = 0

    @ttl_cache(ttl_seconds=10)
    def expensive(x: int) -> int:
        nonlocal call_count
        call_count += 1
        return x * 2

    assert expensive(5) == 10
    assert expensive(5) == 10
    assert call_count == 1


def test_cache_different_args_separate_entries() -> None:
    call_count = 0

    @ttl_cache(ttl_seconds=10)
    def fn(x: int) -> int:
        nonlocal call_count
        call_count += 1
        return x

    fn(1)
    fn(2)
    assert call_count == 2


def test_invalidate_all_clears_cache() -> None:
    @ttl_cache(ttl_seconds=60)
    def cached_fn(x: int) -> int:
        return x

    cached_fn(42)
    invalidate_all()
    stats = cache_stats()
    assert stats["total_entries"] == 0


def test_cache_stats_returns_counts() -> None:
    invalidate_all()

    @ttl_cache(ttl_seconds=60)
    def another_fn(x: int) -> int:
        return x

    another_fn(1)
    another_fn(2)
    stats = cache_stats()
    assert stats["total_entries"] >= 2
    assert stats["live_entries"] >= 2
