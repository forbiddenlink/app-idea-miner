import asyncio

from sqlalchemy import func, select

from packages.core.database import AsyncSessionLocal
from packages.core.models import RawPost


async def main():
    print("Verifying ingestion results...")
    async with AsyncSessionLocal() as db:
        # Check for specific Mock Reddit posts
        stmt = select(func.count()).where(RawPost.title.like("[Request]%"))
        result = await db.execute(stmt)
        mock_count = result.scalar_one()
        print(f"Mock Reddit posts ([Request]...): {mock_count}")

        if mock_count > 0:
            stmt = select(RawPost).where(RawPost.title.like("[Request]%")).limit(1)
            result = await db.execute(stmt)
            post = result.scalar_one_or_none()
            print(f"Sample Mock Post: {post.title}")
            print(f"Metadata: {post.source_metadata}")
        else:
            print(
                "FAILURE: No mock posts found. Ingestion plugin did not run or did not generate data."
            )


if __name__ == "__main__":
    asyncio.run(main())
