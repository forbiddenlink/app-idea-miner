"""
Request logging middleware with correlation IDs.

Adds:
- Unique X-Request-ID header to every request/response
- Structured log output with timing, status code, and client info
- Request correlation for distributed tracing
"""

import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("api.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs every request with timing and correlation ID.

    Adds X-Request-ID header to responses for client-side correlation.
    Logs structured access info: method, path, status, duration, client IP.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Generate or accept incoming request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]

        # Record start time
        start_time = time.perf_counter()

        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""

        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Determine log level based on status code
            status_code = response.status_code
            if status_code >= 500:
                log_level = logging.ERROR
            elif status_code >= 400:
                log_level = logging.WARNING
            else:
                log_level = logging.INFO

            # Log structured entry (skip noisy health check successes)
            is_health_check = path in ("/health", "/metrics") and status_code < 400
            if not is_health_check:
                log_data = {
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "query": query,
                    "status": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                }

                logger.log(
                    log_level,
                    "%(method)s %(path)s %(status)s %(duration_ms)sms [%(request_id)s]",
                    log_data,
                )

            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "%s %s 500 %sms [%s] error=%s",
                method,
                path,
                duration_ms,
                request_id,
                str(exc),
            )
            raise
