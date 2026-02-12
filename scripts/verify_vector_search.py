import asyncio
import os
import random
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.services.idea_service import IdeaService
from packages.core.models import IdeaCandidate, RawPost

# Use local docker DB
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/appideas"


async def main():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        service = IdeaService(db)

        # 1. Cleanup old test data
        print("Cleaning up old test data...")
        await db.execute(
            text(
                "DELETE FROM idea_candidates WHERE problem_statement LIKE 'TEST_VECTOR_%'"
            )
        )
        await db.execute(text("DELETE FROM raw_posts WHERE title LIKE 'TEST_VECTOR_%'"))
        await db.commit()

        # 2. Insert dummy data with vectors
        print("Inserting test data...")

        # Vector A: [1, 0, 0, ... 0] (1536 dims)
        vec_a = [0.0] * 1536
        vec_a[0] = 1.0

        # Vector B: [0, 1, 0, ... 0] (Orthogonal to A)
        vec_b = [0.0] * 1536
        vec_b[1] = 1.0

        # Vector C: [0.9, 0.1, 0, ... 0] (Similar to A)
        vec_c = [0.0] * 1536
        vec_c[0] = 0.9
        vec_c[1] = 0.1

        post = RawPost(
            title="TEST_VECTOR_POST",
            url=f"http://test.com/{uuid4()}",
            url_hash="hash",
            source="test",
            content="content",
        )
        db.add(post)
        await db.flush()

        idea_a = IdeaCandidate(
            raw_post_id=post.id,
            problem_statement="TEST_VECTOR_A",
            sentiment="neutral",
            sentiment_score=0,
            quality_score=0.5,
            idea_vector=vec_a,
        )
        idea_b = IdeaCandidate(
            raw_post_id=post.id,
            problem_statement="TEST_VECTOR_B",
            sentiment="neutral",
            sentiment_score=0,
            quality_score=0.5,
            idea_vector=vec_b,
        )
        db.add_all([idea_a, idea_b])
        await db.commit()

        # 3. Test Vector Search (Query close to A)
        print("\nTesting Semantic Search (Query similar to A)...")
        results = await service.search_ideas(q="ignored", query_vector=vec_c, limit=5)

        print(f"Found {len(results['results'])} results.")
        for idea in results["results"]:
            print(f" - {idea.problem_statement} (Score: {idea.similarity_score:.4f})")

        # Verify A is ranked higher than B
        first = results["results"][0]
        if first.problem_statement == "TEST_VECTOR_A":
            print("SUCCESS: Vector A ranked first!")
        else:
            print(f"FAILURE: Expected vector A first, got {first.problem_statement}")

        # 4. Cleanup
        print("\nCleaning up...")
        await db.execute(
            text(
                "DELETE FROM idea_candidates WHERE problem_statement LIKE 'TEST_VECTOR_%'"
            )
        )
        await db.execute(text("DELETE FROM raw_posts WHERE title LIKE 'TEST_VECTOR_%'"))
        await db.commit()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
