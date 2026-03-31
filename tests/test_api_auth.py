import pytest
from httpx import AsyncClient

from apps.api.app.core.auth import create_access_token, get_password_hash
from packages.core.models import User

pytestmark = pytest.mark.requires_db


@pytest.mark.asyncio
async def test_register_returns_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_normalizes_email_and_rejects_case_duplicate(
    client: AsyncClient,
):
    first = await client.post(
        "/api/v1/auth/register",
        json={"email": "CaseUser@example.com", "password": "password123"},
    )
    assert first.status_code == 201

    duplicate = await client.post(
        "/api/v1/auth/register",
        json={"email": "caseuser@example.com", "password": "password123"},
    )
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_login_success_and_me(client: AsyncClient, db_session):
    user = User(
        email="login@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "LOGIN@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    me_payload = me_response.json()
    assert me_payload["email"] == "login@example.com"


@pytest.mark.asyncio
async def test_login_rejects_bad_password(client: AsyncClient, db_session):
    user = User(
        email="badpass@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "badpass@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_rejects_inactive_user(client: AsyncClient, db_session):
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "password123"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_rejects_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_rejects_token_for_missing_user(client: AsyncClient):
    token = create_access_token({"sub": "11111111-1111-1111-1111-111111111111"})
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
