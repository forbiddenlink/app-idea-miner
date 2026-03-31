import pytest
from httpx import AsyncClient

from apps.api.app.config import get_settings
from apps.api.app.core.auth import create_access_token, get_password_hash
from packages.core.models import Cluster, IdeaCandidate, RawPost, User

pytestmark = pytest.mark.requires_db

settings = get_settings()
API_KEY_HEADER = {"X-API-Key": settings.API_KEY}


async def auth_headers(
    db_session, email: str = "bookmarks@example.com"
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
async def test_bookmarks_require_api_key(client: AsyncClient):
    response = await client.get("/api/v1/bookmarks")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_bookmarks_require_auth(client: AsyncClient):
    response = await client.get("/api/v1/bookmarks", headers=API_KEY_HEADER)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_list_delete_cluster_bookmark(client: AsyncClient, db_session):
    headers = await auth_headers(db_session)
    cluster = Cluster(
        label="Saved Cluster",
        description="A cluster worth revisiting",
        keywords=["saved", "cluster"],
        idea_count=12,
        avg_sentiment=0.3,
        quality_score=0.8,
        trend_score=0.6,
    )
    db_session.add(cluster)
    await db_session.commit()

    create_response = await client.post(
        "/api/v1/bookmarks",
        headers=headers,
        json={
            "item_type": "cluster",
            "item_id": str(cluster.id),
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["success"] is True

    list_response = await client.get(
        "/api/v1/bookmarks",
        headers=headers,
    )
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["pagination"]["total"] == 1
    assert payload["bookmarks"][0]["item_type"] == "cluster"
    assert payload["bookmarks"][0]["cluster"]["label"] == "Saved Cluster"

    delete_response = await client.delete(
        f"/api/v1/bookmarks/cluster/{cluster.id}",
        headers=headers,
    )
    assert delete_response.status_code == 200

    list_after_delete = await client.get(
        "/api/v1/bookmarks",
        headers=headers,
    )
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["bookmarks"] == []


@pytest.mark.asyncio
async def test_list_idea_bookmark_returns_embedded_idea(
    client: AsyncClient, db_session
):
    headers = await auth_headers(db_session, email="ideas@example.com")
    post = RawPost(
        url="https://example.com/bookmarked-idea",
        url_hash="bookmarked-idea",
        title="Bookmarked Idea Source",
        source="test",
    )
    db_session.add(post)
    await db_session.flush()

    idea = IdeaCandidate(
        raw_post_id=post.id,
        problem_statement="Need a better reminder app",
        context="Users forget recurring tasks",
        sentiment="positive",
        sentiment_score=0.7,
        quality_score=0.85,
        domain="productivity",
    )
    db_session.add(idea)
    await db_session.commit()

    create_response = await client.post(
        "/api/v1/bookmarks",
        headers=headers,
        json={
            "item_type": "idea",
            "item_id": str(idea.id),
        },
    )
    assert create_response.status_code == 201

    list_response = await client.get(
        "/api/v1/bookmarks?item_type=idea",
        headers=headers,
    )
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["pagination"]["total"] == 1
    item = payload["bookmarks"][0]
    assert item["item_type"] == "idea"
    assert item["idea"]["problem_statement"] == "Need a better reminder app"
    assert item["idea"]["raw_post"]["url"] == "https://example.com/bookmarked-idea"


@pytest.mark.asyncio
async def test_clear_bookmarks_removes_scope_items(client: AsyncClient, db_session):
    headers = await auth_headers(db_session, email="clear@example.com")
    cluster = Cluster(
        label="Clear Target",
        description="Cluster to clear",
        keywords=["clear"],
        idea_count=1,
        avg_sentiment=0.1,
        quality_score=0.4,
        trend_score=0.2,
    )
    db_session.add(cluster)
    await db_session.commit()

    for _ in range(2):
        await client.post(
            "/api/v1/bookmarks",
            headers=headers,
            json={
                "item_type": "cluster",
                "item_id": str(cluster.id),
            },
        )

    clear_response = await client.delete(
        "/api/v1/bookmarks",
        headers=headers,
    )
    assert clear_response.status_code == 200
    assert clear_response.json()["success"] is True

    list_response = await client.get(
        "/api/v1/bookmarks",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert list_response.json()["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_create_bookmark_not_found_returns_404(client: AsyncClient):
    # Missing auth returns 401 before item lookup
    response = await client.post(
        "/api/v1/bookmarks",
        headers=API_KEY_HEADER,
        json={
            "item_type": "cluster",
            "item_id": "11111111-1111-1111-1111-111111111111",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_bookmark_not_found_returns_404_when_authenticated(
    client: AsyncClient, db_session
):
    headers = await auth_headers(db_session, email="missing@example.com")
    response = await client.post(
        "/api/v1/bookmarks",
        headers=headers,
        json={
            "item_type": "cluster",
            "item_id": "11111111-1111-1111-1111-111111111111",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_bookmarks_are_isolated_by_authenticated_user(
    client: AsyncClient, db_session
):
    headers_a = await auth_headers(db_session, email="user-a@example.com")
    headers_b = await auth_headers(db_session, email="user-b@example.com")

    cluster = Cluster(
        label="Private Cluster",
        description="Only user A should see this",
        keywords=["private"],
        idea_count=1,
        avg_sentiment=0.1,
        quality_score=0.5,
        trend_score=0.2,
    )
    db_session.add(cluster)
    await db_session.commit()

    create_response = await client.post(
        "/api/v1/bookmarks",
        headers=headers_a,
        json={"item_type": "cluster", "item_id": str(cluster.id)},
    )
    assert create_response.status_code == 201

    user_b_list = await client.get("/api/v1/bookmarks", headers=headers_b)
    assert user_b_list.status_code == 200
    assert user_b_list.json()["bookmarks"] == []
