import asyncio
import logging
import os
import sys

# Ensure packages can be imported
sys.path.append(os.getcwd())

from apps.worker.sources.reddit import RedditSource

logging.basicConfig(level=logging.INFO)


async def main():
    print("Testing Reddit Source...")
    source = RedditSource()

    if source.is_mock:
        print("Running in MOCK mode (no credentials found).")
    else:
        print("Running in REAL mode.")

    posts = await source.fetch()

    print(f"Fetched {len(posts)} posts.")
    for p in posts:
        print(f"- {p.title} ({p.url})")


if __name__ == "__main__":
    asyncio.run(main())
