import pytest
from httpx import AsyncClient

from apps.api.app.config import get_settings
from packages.core.models import IdeaCandidate, RawPost

settings = get_settings()
API_KEY_HEADER = {"X-API-Key": settings.API_KEY}


@pytest.mark.asyncio
async def test_list_ideas_unauthorized(client: AsyncClient):
    """Test accessing ideas without API key fails."""
    response = await client.get("/api/v1/ideas")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_ideas_authorized(client: AsyncClient, db_session):
    """Test accessing ideas with API key succeeds."""
    # Seed data
    post = RawPost(
        url="http://idea.com", url_hash="abc", title="Idea Post", source="test"
    )
    db_session.add(post)
    await db_session.flush()

    idea = IdeaCandidate(
        raw_post_id=post.id,
        problem_statement="Need AI for tests",
        sentiment="positive",
        sentiment_score=0.9,
        quality_score=0.95,
        domain="dev",
    )
    db_session.add(idea)
    await db_session.commit()

    response = await client.get("/api/v1/ideas", headers=API_KEY_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert len(data["ideas"]) == 1
    assert data["ideas"][0]["problem_statement"] == "Need AI for tests"


@pytest.mark.asyncio
async def test_list_ideas_filters_by_q_across_problem_and_context(
    client: AsyncClient, db_session
):
    """Test q filter matches both problem_statement and context."""
    post_1 = RawPost(
        url="http://idea3.com", url_hash="ghi", title="Budgeting Idea", source="test"
    )
    post_2 = RawPost(
        url="http://idea4.com", url_hash="jkl", title="Fitness Idea", source="test"
    )
    db_session.add_all([post_1, post_2])
    await db_session.flush()

    db_session.add_all(
        [
            IdeaCandidate(
                raw_post_id=post_1.id,
                problem_statement="Need a better budgeting planner",
                context="Teams still track cashflow manually in CSV sheets",
                sentiment="positive",
                sentiment_score=0.6,
                quality_score=0.75,
                domain="finance",
            ),
            IdeaCandidate(
                raw_post_id=post_2.id,
                problem_statement="Workout accountability reminder app",
                context="Gym buddies forget sessions",
                sentiment="neutral",
                sentiment_score=0.1,
                quality_score=0.55,
                domain="health",
            ),
        ]
    )
    await db_session.commit()

    response_problem = await client.get(
        "/api/v1/ideas?q=budget", headers=API_KEY_HEADER
    )
    assert response_problem.status_code == 200
    problem_payload = response_problem.json()
    assert len(problem_payload["ideas"]) == 1
    assert "budgeting" in problem_payload["ideas"][0]["problem_statement"].lower()

    response_context = await client.get("/api/v1/ideas?q=csv", headers=API_KEY_HEADER)
    assert response_context.status_code == 200
    context_payload = response_context.json()
    assert len(context_payload["ideas"]) == 1
    assert "budgeting" in context_payload["ideas"][0]["problem_statement"].lower()


@pytest.mark.asyncio
async def test_list_ideas_supports_sorting(client: AsyncClient, db_session):
    """Test sort_by and order parameters influence result order."""
    post_1 = RawPost(
        url="http://idea5.com", url_hash="mno", title="Idea A", source="test"
    )
    post_2 = RawPost(
        url="http://idea6.com", url_hash="pqr", title="Idea B", source="test"
    )
    db_session.add_all([post_1, post_2])
    await db_session.flush()

    db_session.add_all(
        [
            IdeaCandidate(
                raw_post_id=post_1.id,
                problem_statement="Low quality but high sentiment",
                sentiment="positive",
                sentiment_score=0.9,
                quality_score=0.2,
                domain="social",
            ),
            IdeaCandidate(
                raw_post_id=post_2.id,
                problem_statement="High quality but lower sentiment",
                sentiment="neutral",
                sentiment_score=0.1,
                quality_score=0.9,
                domain="social",
            ),
        ]
    )
    await db_session.commit()

    by_quality = await client.get(
        "/api/v1/ideas?sort_by=quality&order=asc&limit=2", headers=API_KEY_HEADER
    )
    assert by_quality.status_code == 200
    quality_payload = by_quality.json()
    assert len(quality_payload["ideas"]) == 2
    assert (
        quality_payload["ideas"][0]["quality_score"]
        <= quality_payload["ideas"][1]["quality_score"]
    )

    by_sentiment = await client.get(
        "/api/v1/ideas?sort_by=sentiment&order=desc&limit=2", headers=API_KEY_HEADER
    )
    assert by_sentiment.status_code == 200
    sentiment_payload = by_sentiment.json()
    assert len(sentiment_payload["ideas"]) == 2
    assert (
        sentiment_payload["ideas"][0]["sentiment_score"]
        >= sentiment_payload["ideas"][1]["sentiment_score"]
    )


@pytest.mark.asyncio
async def test_get_idea_by_id(client: AsyncClient, db_session):
    """Test retrieving a single idea."""
    post = RawPost(
        url="http://idea2.com", url_hash="def", title="Idea Post 2", source="test"
    )
    db_session.add(post)
    await db_session.flush()

    idea = IdeaCandidate(
        raw_post_id=post.id,
        problem_statement="Another idea",
        sentiment="neutral",
        sentiment_score=0.0,
        quality_score=0.5,
        domain="social",
    )
    db_session.add(idea)
    await db_session.commit()

    # Get ID as string
    idea_id = str(idea.id)

    response = await client.get(f"/api/v1/ideas/{idea_id}", headers=API_KEY_HEADER)
    assert response.status_code == 200
    assert response.json()["id"] == idea_id
