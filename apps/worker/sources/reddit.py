import logging
import os
import random
from datetime import UTC, datetime, timezone

import asyncpraw

from apps.worker.sources.base import BaseSource
from packages.core.dedupe import generate_url_hash
from packages.core.models import RawPost

logger = logging.getLogger(__name__)


class RedditSource(BaseSource):
    """
    Fetches posts from Reddit using asyncpraw.
    """

    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "AppIdeaMiner/0.1.0")

        if not self.client_id or not self.client_secret:
            logger.warning("Reddit credentials not found. Falling back to MOCK mode.")
            self.is_mock = True
        else:
            self.is_mock = False

    async def fetch(self) -> list[RawPost]:
        if self.is_mock:
            return await self._fetch_mock()

        logger.info("Fetching from Reddit API...")
        fetched_posts = []

        try:
            reddit = asyncpraw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
            )

            # Subreddits to monitor
            subreddits = ["AppIdeas", "StartupIdeas", "SomebodyMakeThis", "SideProject"]
            subreddit_str = "+".join(subreddits)

            subreddit = await reddit.subreddit(subreddit_str)

            # Fetch new posts (limit to 50 combined)
            async for submission in subreddit.new(limit=50):
                # Skip stickied posts
                if submission.stickied:
                    continue

                # Convert timestamp
                published_at = datetime.fromtimestamp(submission.created_utc, tz=UTC)

                # Create wrapper for raw post
                url = f"https://www.reddit.com{submission.permalink}"

                post = RawPost(
                    url=url,
                    url_hash=generate_url_hash(url),
                    title=submission.title,
                    content=submission.selftext or "",
                    source="reddit",
                    author=str(submission.author),
                    published_at=published_at,
                    fetched_at=datetime.now(UTC),
                    source_metadata={
                        "subreddit": submission.subreddit.display_name,
                        "upvotes": submission.score,
                        "comments": submission.num_comments,
                        "id": submission.id,
                    },
                    is_processed=False,
                )
                fetched_posts.append(post)

            await reddit.close()
            logger.info(f"Fetched {len(fetched_posts)} posts from Reddit.")

        except Exception as e:
            logger.error(f"Error fetching from Reddit: {e}", exc_info=True)

        return fetched_posts

    async def _fetch_mock(self) -> list[RawPost]:
        """Keep mock implementation for standalone testing without creds"""
        logger.info("Fetching from Reddit (Mock Mode)...")
        from uuid import uuid4

        mock_ideas = [
            ("I need an app that tracks my sourdough starter", "r/Sourdough"),
            ("Uber, but for pet iguanas", "r/SideProject"),
            ("A social network for ghosts", "r/CrazyIdeas"),
        ]

        fetched_posts = []
        idea, subreddit = random.choice(mock_ideas)
        url = f"https://reddit.com/{subreddit}/comments/{str(uuid4())[:6]}"

        post = RawPost(
            url=url,
            url_hash=generate_url_hash(url),
            title=f"[Request] {idea}",
            content=f"Basically {idea}. Does this exist?",
            source="reddit",
            author="mock_user",
            published_at=datetime.now(UTC),
            fetched_at=datetime.now(UTC),
            source_metadata={
                "subreddit": subreddit,
                "upvotes": random.randint(1, 400),
                "comments": random.randint(0, 50),
            },
            is_processed=False,
        )
        fetched_posts.append(post)
        return fetched_posts
