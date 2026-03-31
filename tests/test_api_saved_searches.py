import pytest
from httpx import AsyncClient

from apps.api.app.config import get_settings
from apps.api.app.core.auth import create_access_token, get_password_hash
from packages.core.models import User

pytestmark = pytest.mark.requires_db

settings = get_settings()
API_KEY_HEADER = {"X-API-Key": settings.API_KEY}


async def auth_headers(
    db_session, email: str = "saved-searches@example.com"
) -> dict[str, str]:
    user = User(
        email=email,
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    token = create_access_token({"sub": str(user.id)})
    return {
        **API_KEY_HEADER,
        "Authorization": f"Bearer {token}",
    }


@pytest.mark.asyncio
async def test_saved_searches_require_api_key(client: AsyncClient):
    response = await client.get("/api/v1/saved-searches")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_saved_searches_require_auth(client: AsyncClient):
    response = await client.get("/api/v1/saved-searches", headers=API_KEY_HEADER)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_list_update_delete_saved_search(client: AsyncClient, db_session):
    headers = await auth_headers(db_session)

    create_response = await client.post(
        "/api/v1/saved-searches",
        headers=headers,
        json={
            "name": "High quality fintech",
            "query_params": {"domain": "fintech", "min_quality": 0.8},
            "alert_enabled": True,
            "alert_frequency": "daily",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()["saved_search"]
    saved_search_id = created["id"]
    assert created["name"] == "High quality fintech"

    list_response = await client.get("/api/v1/saved-searches", headers=headers)
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["pagination"]["total"] == 1
    assert payload["saved_searches"][0]["id"] == saved_search_id

    update_response = await client.patch(
        f"/api/v1/saved-searches/{saved_search_id}",
        headers=headers,
        json={"name": "Updated fintech", "alert_frequency": "weekly"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()["saved_search"]
    assert updated["name"] == "Updated fintech"
    assert updated["alert_frequency"] == "weekly"

    delete_response = await client.delete(
        f"/api/v1/saved-searches/{saved_search_id}", headers=headers
    )
    assert delete_response.status_code == 200

    list_after_delete = await client.get("/api/v1/saved-searches", headers=headers)
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["saved_searches"] == []


@pytest.mark.asyncio
async def test_saved_searches_isolated_by_user(client: AsyncClient, db_session):
    headers_a = await auth_headers(db_session, email="saved-a@example.com")
    headers_b = await auth_headers(db_session, email="saved-b@example.com")

    create_response = await client.post(
        "/api/v1/saved-searches",
        headers=headers_a,
        json={"name": "A only", "query_params": {"q": "billing"}},
    )
    assert create_response.status_code == 201

    user_b_list = await client.get("/api/v1/saved-searches", headers=headers_b)
    assert user_b_list.status_code == 200
    assert user_b_list.json()["saved_searches"] == []
