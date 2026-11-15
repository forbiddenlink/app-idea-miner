"""Server-side attachment of X-API-Key for same-origin browser requests."""

from types import SimpleNamespace

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from apps.api.app.core import browser_key
from apps.api.app.core.browser_key import ServerSideApiKeyMiddleware
from apps.api.app.core.security import get_api_key

SERVER_KEY = "server-only-key-0123456789"


def _settings(api_key=SERVER_KEY, env="production"):
    return SimpleNamespace(
        API_KEY=api_key,
        ENV=env,
        CORS_ORIGINS=["https://app-idea-miner.vercel.app"],
    )


def _app(monkeypatch, settings):
    monkeypatch.setattr(browser_key, "get_settings", lambda: settings)
    monkeypatch.setattr(
        "apps.api.app.core.security.settings", SimpleNamespace(API_KEY=SERVER_KEY)
    )
    app = FastAPI()
    app.add_middleware(ServerSideApiKeyMiddleware)

    @app.get("/api/v1/thing", dependencies=[Depends(get_api_key)])
    async def thing():
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"ok": True}

    return app


async def _get(app, path, headers=None):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        return await ac.get(path, headers=headers or {})


@pytest.mark.asyncio
async def test_same_origin_browser_request_gets_key_attached(monkeypatch):
    app = _app(monkeypatch, _settings())
    r = await _get(app, "/api/v1/thing", {"Sec-Fetch-Site": "same-origin"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_allowed_origin_gets_key_attached(monkeypatch):
    app = _app(monkeypatch, _settings())
    r = await _get(
        app, "/api/v1/thing", {"Origin": "https://app-idea-miner.vercel.app"}
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_foreign_origin_is_not_given_the_key(monkeypatch):
    app = _app(monkeypatch, _settings())
    r = await _get(app, "/api/v1/thing", {"Origin": "https://evil.example"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_bare_request_without_browser_signals_is_rejected(monkeypatch):
    app = _app(monkeypatch, _settings())
    r = await _get(app, "/api/v1/thing")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_missing_server_key_fails_closed(monkeypatch):
    app = _app(monkeypatch, _settings(api_key=""))
    r = await _get(app, "/api/v1/thing", {"Sec-Fetch-Site": "same-origin"})
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_default_dev_key_in_production_fails_closed(monkeypatch):
    app = _app(monkeypatch, _settings(api_key="dev-api-key"))
    r = await _get(app, "/api/v1/thing", {"Sec-Fetch-Site": "same-origin"})
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_non_api_paths_untouched(monkeypatch):
    app = _app(monkeypatch, _settings(api_key=""))
    r = await _get(app, "/health", {"Sec-Fetch-Site": "same-origin"})
    assert r.status_code == 200
