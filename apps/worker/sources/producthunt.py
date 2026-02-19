import logging
import os
import random
from datetime import UTC, datetime, timezone
from uuid import uuid4

import httpx

from apps.worker.sources.base import BaseSource
from packages.core.dedupe import generate_url_hash
from packages.core.models import RawPost

logger = logging.getLogger(__name__)


class ProductHuntSource(BaseSource):
    """
    Fetches posts from Product Hunt using their GraphQL API.
    """

    def __init__(self):
        self.api_token = os.getenv("PRODUCT_HUNT_TOKEN")
        self.api_url = "https://api.producthunt.com/v2/api/graphql"

        if not self.api_token:
            logger.warning("Product Hunt token not found. Falling back to MOCK mode.")
            self.is_mock = True
        else:
            self.is_mock = False

    async def fetch(self) -> list[RawPost]:
        if self.is_mock:
            return await self._fetch_mock()

        logger.info("Fetching from Product Hunt API...")
        fetched_posts = []

        query = """
        query {
          posts(first: 20, order: VOTES) {
            edges {
              node {
                id
                name
                tagline
                url
                votesCount
                commentsCount
                createdAt
                topics {
                  edges {
                    node {
                      name
                    }
                  }
                }
                user {
                  name
                }
              }
            }
          }
        }
        """

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                # Retry logic for transient failures
                last_error = None
                for attempt in range(3):
                    try:
                        response = await client.post(
                            self.api_url,
                            json={"query": query},
                            headers=headers,
                            timeout=30.0,  # Increased timeout
                        )
                        response.raise_for_status()
                        data = response.json()
                        break  # Success, exit retry loop
                    except httpx.HTTPStatusError as e:
                        last_error = e
                        # Retry on 5xx server errors
                        if 500 <= e.response.status_code < 600:
                            logger.warning(
                                f"Product Hunt API server error (attempt {attempt + 1}/3): "
                                f"{e.response.status_code}"
                            )
                            if attempt < 2:
                                import asyncio

                                await asyncio.sleep(2**attempt)  # Exponential backoff
                                continue
                        # Don't retry client errors (4xx)
                        raise
                    except httpx.TimeoutException as e:
                        last_error = e
                        logger.warning(
                            f"Product Hunt API timeout (attempt {attempt + 1}/3)"
                        )
                        if attempt < 2:
                            import asyncio

                            await asyncio.sleep(2**attempt)
                            continue
                        raise
                else:
                    # All retries exhausted
                    if last_error:
                        raise last_error

                if "errors" in data:
                    logger.error(f"Product Hunt API errors: {data['errors']}")
                    return []

                posts_data = data.get("data", {}).get("posts", {}).get("edges", [])

                for edge in posts_data:
                    node = edge["node"]

                    # Extract topics
                    topics = [
                        t["node"]["name"]
                        for t in node.get("topics", {}).get("edges", [])
                    ]

                    # Parse timestamp (PH format: 2023-11-22T08:00:00Z)
                    published_at = datetime.fromisoformat(
                        node["createdAt"].replace("Z", "+00:00")
                    )

                    # Create RawPost
                    post = RawPost(
                        url=node["url"],
                        url_hash=generate_url_hash(node["url"]),
                        title=f"{node['name']} - {node['tagline']}",
                        content=node[
                            "tagline"
                        ],  # PH posts don't have body text in list view
                        source="producthunt",
                        author=node["user"]["name"],
                        published_at=published_at,
                        fetched_at=datetime.now(UTC),
                        source_metadata={
                            "votesCount": node["votesCount"],
                            "commentsCount": node["commentsCount"],
                            "topics": topics,
                            "id": node["id"],
                        },
                        is_processed=False,
                    )
                    fetched_posts.append(post)

            logger.info(f"Fetched {len(fetched_posts)} posts from Product Hunt.")

        except Exception as e:
            logger.error(f"Error fetching from Product Hunt: {e}", exc_info=True)

        return fetched_posts

    async def _fetch_mock(self) -> list[RawPost]:
        """Keep mock implementation for standalone testing without creds"""
        logger.info("Fetching from Product Hunt (Mock Mode)...")

        mock_products = [
            ("AI-Powered Toaster", "Perfect toast every time using computer vision"),
            ("Notion for Cats", "Organize your feline's life"),
            (
                "Zoom wrapper that makes you look awake",
                "Deepfake yourself into attention",
            ),
        ]

        fetched_posts = []
        name, tagline = random.choice(mock_products)
        url = f"https://producthunt.com/posts/{name.lower().replace(' ', '-')}-{str(uuid4())[:4]}"

        post = RawPost(
            url=url,
            url_hash=generate_url_hash(url),
            title=f"{name} - {tagline}",
            content=tagline,
            source="producthunt",
            author="maker_mock",
            published_at=datetime.now(UTC),
            fetched_at=datetime.now(UTC),
            source_metadata={
                "votesCount": random.randint(100, 5000),
                "commentsCount": random.randint(10, 200),
                "topics": ["productivity", "ai", "tech"],
            },
            is_processed=False,
        )
        fetched_posts.append(post)

        return fetched_posts
