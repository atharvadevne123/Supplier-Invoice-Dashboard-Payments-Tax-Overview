"""Tests for the rate-limiting module."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app import rate_limit as rl


def _make_request(ip: str = "127.0.0.1") -> MagicMock:
    req = MagicMock()
    req.headers = {}
    req.client = MagicMock()
    req.client.host = ip
    return req


def test_rate_limit_allows_under_limit() -> None:
    rl._request_counts.clear()
    req = _make_request("10.0.0.1")
    for _ in range(5):
        rl.check_rate_limit(req)


def test_rate_limit_blocks_over_limit() -> None:
    rl._request_counts.clear()
    old_limit = rl.RATE_LIMIT
    rl.RATE_LIMIT = 3
    req = _make_request("10.0.0.2")
    try:
        for _ in range(3):
            rl.check_rate_limit(req)
        with pytest.raises(HTTPException) as exc:
            rl.check_rate_limit(req)
        assert exc.value.status_code == 429
    finally:
        rl.RATE_LIMIT = old_limit
        rl._request_counts.clear()


def test_rate_limit_uses_forwarded_for() -> None:
    rl._request_counts.clear()
    req = MagicMock()
    req.headers = {"X-Forwarded-For": "203.0.113.5, 10.0.0.1"}
    req.client = MagicMock()
    req.client.host = "10.0.0.1"
    rl.check_rate_limit(req)
    assert "203.0.113.5" in rl._request_counts
