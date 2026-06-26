"""Simple in-memory rate limiting for the API."""

import logging
import time
from collections import defaultdict

from fastapi import HTTPException, Request

from app.config import settings

logger = logging.getLogger(__name__)

_request_counts: dict[str, list[float]] = defaultdict(list)

RATE_LIMIT: int = settings.rate_limit
WINDOW_SECONDS: int = settings.window_seconds


def check_rate_limit(request: Request) -> None:
    """Raise HTTP 429 if client exceeds RATE_LIMIT requests per WINDOW_SECONDS.

    Uses the client IP (X-Forwarded-For or direct) as the rate-limit key.
    Expired timestamps outside the current window are pruned on each call.

    Args:
        request: Incoming FastAPI request used to extract client IP.

    Raises:
        HTTPException: 429 with Retry-After header if rate limit exceeded.
    """
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )
    now = time.monotonic()
    window_start = now - WINDOW_SECONDS
    timestamps = _request_counts[client_ip]
    _request_counts[client_ip] = [t for t in timestamps if t > window_start]
    _request_counts[client_ip].append(now)
    count = len(_request_counts[client_ip])
    if count > RATE_LIMIT:
        logger.warning("Rate limit exceeded: client=%s count=%d", client_ip, count)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {RATE_LIMIT} requests per {WINDOW_SECONDS}s",
            headers={"Retry-After": str(WINDOW_SECONDS)},
        )
