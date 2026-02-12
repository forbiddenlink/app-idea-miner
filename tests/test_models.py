import pytest
from sqlalchemy import select

from packages.core.models import IdeaCandidate, RawPost


@pytest.mark.asyncio
async def test_create_raw_post(db_session):
    """Test creating a RawPost."""
    post = RawPost(
        url="https://example.com/post-1",
        url_hash="hash123",
        title="Test Post Title",
        content="This is some content",
        source="test_source",
    )
    db_session.add(post)
    await db_session.commit()

    # Refresh/Fetch
    stmt = select(RawPost).where(RawPost.url == "https://example.com/post-1")
    result = await db_session.execute(stmt)
    fetched_post = result.scalar_one()

    assert fetched_post.title == "Test Post Title"
    assert fetched_post.id is not None
    assert fetched_post.created_at is not None


@pytest.mark.asyncio
async def test_create_idea_candidate(db_session):
    """Test creating an IdeaCandidate linked to a post."""
    # Create parent post
    post = RawPost(
        url="https://example.com/post-2",
        url_hash="hash456",
        title="Another Post",
        source="test_source",
    )
    db_session.add(post)
    await db_session.flush()  # get ID

    # Create idea
    idea = IdeaCandidate(
        raw_post_id=post.id,
        problem_statement="People need better testing tools",
        sentiment="positive",
        sentiment_score=0.8,
        quality_score=0.9,
        domain="developer_tools",
    )
    db_session.add(idea)
    await db_session.commit()

    # Verify relationship
    stmt = select(IdeaCandidate).where(
        IdeaCandidate.problem_statement == "People need better testing tools"
    )
    result = await db_session.execute(stmt)
    fetched_idea = result.scalar_one()

    assert fetched_idea.raw_post_id == post.id
    assert fetched_idea.domain == "developer_tools"
