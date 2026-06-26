"""Custom FastAPI middleware: request correlation ID and structured access logging."""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Correlation-ID header to every request and response.

    If the client supplies an X-Correlation-ID request header, it is echoed back;
    otherwise a new UUID4 is generated. The middleware also logs method, path,
    status code, and duration for each request.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Inject correlation ID header and log request duration.

        Args:
            request: Incoming HTTP request.
            call_next: ASGI callable for the next middleware or route handler.

        Returns:
            HTTP response with X-Correlation-ID header set.
        """
        correlation_id = request.headers.get("X-Correlation-ID") or uuid.uuid4().hex
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Correlation-ID"] = correlation_id
        logger.info(
            "method=%s path=%s status=%d duration_ms=%.1f correlation_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            correlation_id,
        )
        return response
