"""
Server-side X-API-Key attachment for the web app.

The browser bundle must not carry an API key: every VITE_* variable is inlined
into public JavaScript, so a key set there is readable by anyone. Instead the
web app calls the same-origin /api/v1 path without a key and this middleware
attaches the server-only ``API_KEY`` before the request reaches the
``get_api_key`` dependency.

Limits (be honest about what this protects): the browser signals used here
(Sec-Fetch-Site, Origin) can be forged by a non-browser client, so this keeps
the key out of the public bundle and allows rotation, but it is not a
substitute for the per-IP RateLimiter already on every router. Callers that
send their own X-API-Key (CI, server-to-server) are passed through untouched.

Fails closed: if the server key is empty, or is still the development default
in production, browser requests get 503 instead of being let through.
"""

import json

from starlette.types import ASGIApp, Receive, Scope, Send

from apps.api.app.config import get_settings

API_PREFIX = "/api/v1/"
DEV_DEFAULT_KEY = "dev-api-key"


def _is_browser_request(
    headers: dict[bytes, bytes], allowed_origins: list[str]
) -> bool:
    if headers.get(b"sec-fetch-site", b"").lower() == b"same-origin":
        return True
    origin = headers.get(b"origin", b"").decode("latin-1")
    return bool(origin) and origin in allowed_origins


class ServerSideApiKeyMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith(API_PREFIX):
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        if b"x-api-key" in headers:
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        origins = settings.CORS_ORIGINS
        if not isinstance(origins, list):
            origins = [origins]
        if not _is_browser_request(headers, origins):
            await self.app(scope, receive, send)
            return

        key = settings.API_KEY
        if not key or (settings.ENV == "production" and key == DEV_DEFAULT_KEY):
            body = json.dumps({"detail": "API key not configured on server"}).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 503,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return

        scope = dict(scope)
        scope["headers"] = [*scope["headers"], (b"x-api-key", key.encode())]
        await self.app(scope, receive, send)
