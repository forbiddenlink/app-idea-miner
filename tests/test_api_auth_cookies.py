"""
Tests for the JWT-in-httpOnly-cookie migration.

The access token used to live in the frontend's localStorage (XSS-readable).
It now lives in an httpOnly, Secure, SameSite=Lax cookie the browser attaches
automatically; a separate double-submit CSRF cookie protects state-changing
cookie-authenticated requests. Authorization-header (Bearer) auth is kept as
a fallback for non-browser callers (see apps/api/app/core/auth.py).
"""

import pytest
from httpx import AsyncClient

from apps.api.app.config import get_settings
from apps.api.app.core.auth import (
    ACCESS_TOKEN_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    get_password_hash,
)
from packages.core.models import User

pytestmark = pytest.mark.requires_db

API_KEY_HEADER = {"X-API-Key": get_settings().API_KEY}


async def _create_active_user(db_session, email: str, password: str = "password123"):
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.mark.asyncio
async def test_login_sets_httponly_secure_samesite_cookie(
    client: AsyncClient, db_session
):
    await _create_active_user(db_session, "cookie-login@example.com")

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "cookie-login@example.com", "password": "password123"},
    )
    assert response.status_code == 200

    set_cookie_headers = response.headers.get_list("set-cookie")
    access_cookie_header = next(
        h for h in set_cookie_headers if h.startswith(f"{ACCESS_TOKEN_COOKIE_NAME}=")
    )
    assert "HttpOnly" in access_cookie_header
    assert "Secure" in access_cookie_header
    assert "SameSite=lax" in access_cookie_header.lower().replace(
        "samesite=lax", "SameSite=lax"
    )
    assert "; path=/" in access_cookie_header.lower()

    # The CSRF cookie must be readable by JS (no HttpOnly) so the frontend
    # can echo it back as a header — that's the whole double-submit design.
    csrf_cookie_header = next(
        h for h in set_cookie_headers if h.startswith(f"{CSRF_COOKIE_NAME}=")
    )
    assert "HttpOnly" not in csrf_cookie_header
    assert "Secure" in csrf_cookie_header


@pytest.mark.asyncio
async def test_authenticated_request_works_via_cookie_alone(
    client: AsyncClient, db_session
):
    await _create_active_user(db_session, "cookie-auth@example.com")
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "cookie-auth@example.com", "password": "password123"},
    )
    assert login.status_code == 200

    # No Authorization header at all — httpx's client cookie jar carries the
    # Set-Cookie from login automatically, exactly like a real browser.
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "cookie-auth@example.com"


@pytest.mark.asyncio
async def test_bearer_header_still_works_for_non_browser_callers(
    client: AsyncClient, db_session
):
    """Backward-compat path: a direct API caller with no cookie jar."""
    await _create_active_user(db_session, "bearer-auth@example.com")
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "bearer-auth@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]

    # Fresh client with no cookies at all, auth via header only.
    from httpx import ASGITransport

    from apps.api.app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as bare_client:
        me = await bare_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me.status_code == 200


@pytest.mark.asyncio
async def test_state_changing_request_without_csrf_header_is_rejected(
    client: AsyncClient, db_session
):
    await _create_active_user(db_session, "csrf-missing@example.com")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "csrf-missing@example.com", "password": "password123"},
    )

    # A cookie-authenticated mutating request with no CSRF header at all.
    response = await client.post(
        "/api/v1/saved-searches",
        json={"name": "test", "query_params": {}},
        headers=API_KEY_HEADER,
    )
    assert response.status_code == 403
    assert "csrf" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_state_changing_request_with_wrong_csrf_header_is_rejected(
    client: AsyncClient, db_session
):
    await _create_active_user(db_session, "csrf-wrong@example.com")
    await client.post(
        "/api/v1/auth/login",
        json={"email": "csrf-wrong@example.com", "password": "password123"},
    )

    response = await client.post(
        "/api/v1/saved-searches",
        json={"name": "test", "query_params": {}},
        headers={**API_KEY_HEADER, CSRF_HEADER_NAME: "not-the-real-token"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_state_changing_request_with_correct_csrf_header_succeeds(
    client: AsyncClient, db_session
):
    await _create_active_user(db_session, "csrf-correct@example.com")
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "csrf-correct@example.com", "password": "password123"},
    )
    csrf_token = login.cookies.get(CSRF_COOKIE_NAME)
    assert csrf_token  # the cookie was actually set

    response = await client.post(
        "/api/v1/saved-searches",
        json={"name": "test search", "query_params": {}},
        headers={**API_KEY_HEADER, CSRF_HEADER_NAME: csrf_token},
    )
    assert response.status_code in (200, 201)


@pytest.mark.asyncio
async def test_bearer_only_caller_is_exempt_from_csrf(client: AsyncClient, db_session):
    """No cookie session means nothing for CSRF to protect."""
    await _create_active_user(db_session, "csrf-bearer@example.com")
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "csrf-bearer@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]

    from httpx import ASGITransport

    from apps.api.app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as bare_client:
        response = await bare_client.post(
            "/api/v1/saved-searches",
            json={"name": "bearer search", "query_params": {}},
            headers={**API_KEY_HEADER, "Authorization": f"Bearer {token}"},
        )
        assert response.status_code in (200, 201)


@pytest.mark.asyncio
async def test_logout_clears_cookies_and_ends_the_session(
    client: AsyncClient, db_session
):
    await _create_active_user(db_session, "logout@example.com")
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "logout@example.com", "password": "password123"},
    )
    csrf_token = login.cookies.get(CSRF_COOKIE_NAME)

    logout_response = await client.post(
        "/api/v1/auth/logout", headers={CSRF_HEADER_NAME: csrf_token}
    )
    assert logout_response.status_code == 204

    set_cookie_headers = logout_response.headers.get_list("set-cookie")
    access_clear = next(
        h for h in set_cookie_headers if h.startswith(f"{ACCESS_TOKEN_COOKIE_NAME}=")
    )
    # A cleared cookie is re-set with an empty value and an expiry in the past.
    assert (
        '=""' in access_clear
        or "=;" in access_clear
        or "Max-Age=0" in access_clear
        or "expires=" in access_clear.lower()
    )

    # The client's cookie jar reflects the clear, so the next request has no
    # session left to authenticate with.
    me_after_logout = await client.get("/api/v1/auth/me")
    assert me_after_logout.status_code == 401
