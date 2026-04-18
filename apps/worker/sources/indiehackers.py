"""
Indie Hackers Source.

Scrapes Indie Hackers discussions for app ideas and pain points.
Focuses on categories where founders discuss problems and needs.
"""

import asyncio
import logging
import re
from datetime import UTC, datetime

import httpx
from bs4 import BeautifulSoup

from apps.worker.sources.base import BaseSource
from packages.core.dedupe import generate_url_hash
from packages.core.models import RawPost

logger = logging.getLogger(__name__)

IH_BASE_URL = "https://www.indiehackers.com"
REQUEST_TIMEOUT = 30.0
MAX_CONCURRENCY = 5

# Categories likely to contain pain points and app ideas
TARGET_CATEGORIES = [
    "product",
    "growth",
    "motivation",
    "land-your-first-sale",
    "productivity-tools",
]

# Keywords that suggest a pain point or app idea
IDEA_KEYWORDS = re.compile(
    r"\b(wish|need|want|looking for|struggle|pain|problem|frustrat|challeng|"
    r"would pay|hate when|anybody know|recommend|alternative|solution|idea|"
    r"build|built|working on|side[\s-]?project|saas)\b",
    re.IGNORECASE,
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class IndieHackersSource(BaseSource):
    """
    Scrapes Indie Hackers group discussions for founder pain points.

    Targets specific categories where app ideas and problems are commonly discussed.
    Uses BeautifulSoup for HTML parsing.
    """

    async def fetch(self) -> list[RawPost]:
        """Fetch posts from Indie Hackers discussion groups."""
        posts: list[RawPost] = []
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as client:
            tasks = [
                self._fetch_category(client, category, semaphore)
                for category in TARGET_CATEGORIES
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Category fetch failed: {result}")
                elif result:
                    posts.extend(result)

        logger.info(f"IndieHackersSource fetched {len(posts)} posts")
        return posts

    async def _fetch_category(
        self,
        client: httpx.AsyncClient,
        category: str,
        semaphore: asyncio.Semaphore,
    ) -> list[RawPost]:
        """Fetch posts from a single category."""
        async with semaphore:
            try:
                url = f"{IH_BASE_URL}/group/{category}"
                logger.debug(f"Fetching {url}")

                response = await client.get(url)
                response.raise_for_status()

                return self._parse_category_page(response.text, category)

            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"HTTP error fetching {category}: {e.response.status_code}"
                )
                return []
            except Exception as e:
                logger.warning(f"Error fetching category {category}: {e}")
                return []

    def _parse_category_page(self, html: str, category: str) -> list[RawPost]:
        """Parse the category page HTML and extract posts."""
        posts: list[RawPost] = []
        soup = BeautifulSoup(html, "html.parser")

        # Find post containers - IH uses various class patterns
        # Try multiple selectors to handle site structure changes
        post_elements = (
            soup.select("article.post")
            or soup.select("div.post-item")
            or soup.select("[data-post-id]")
            or soup.select(".discussion-item")
        )

        if not post_elements:
            # Fallback: look for links that look like discussion links
            post_elements = soup.select('a[href*="/post/"]')

        for element in post_elements[:30]:  # Limit per category
            post = self._parse_post_element(element, category)
            if post:
                posts.append(post)

        logger.debug(f"Parsed {len(posts)} posts from {category}")
        return posts

    def _parse_post_element(self, element, category: str) -> RawPost | None:
        """Parse a single post element into a RawPost."""
        try:
            title_el = (
                element.select_one("h2")
                or element.select_one("h3")
                or element.select_one(".post-title")
                or element.select_one("a")
            )
            if not title_el:
                return None

            title = title_el.get_text(strip=True)
            if not title or len(title) < 10:
                return None

            # Filter for idea-related content
            if not IDEA_KEYWORDS.search(title):
                # Also check content if available
                content_el = element.select_one(".post-content, .post-body, p")
                content_preview = content_el.get_text(strip=True) if content_el else ""
                if not IDEA_KEYWORDS.search(content_preview):
                    return None

            link_el = element.select_one("a[href*='/post/']") or element.find("a")
            if link_el and link_el.get("href"):
                href = link_el["href"]
                url = href if href.startswith("http") else f"{IH_BASE_URL}{href}"
            else:
                url = f"{IH_BASE_URL}/group/{category}#post-{hash(title)}"

            content_el = element.select_one(".post-content, .post-body, .content, p")
            content = content_el.get_text(strip=True) if content_el else title

            author_el = element.select_one(".author, .username, [data-author]")
            author = author_el.get_text(strip=True) if author_el else "unknown"

            likes = 0
            comments = 0

            likes_el = element.select_one(".likes, .upvotes, [data-likes]")
            if likes_el:
                likes_text = likes_el.get_text(strip=True)
                likes_match = re.search(r"(\d+)", likes_text)
                if likes_match:
                    likes = int(likes_match.group(1))

            comments_el = element.select_one(".comments, .replies, [data-comments]")
            if comments_el:
                comments_text = comments_el.get_text(strip=True)
                comments_match = re.search(r"(\d+)", comments_text)
                if comments_match:
                    comments = int(comments_match.group(1))

            return RawPost(
                url=url,
                url_hash=generate_url_hash(url),
                title=title,
                content=content,
                source="indiehackers",
                author=author,
                published_at=None,  # Would need more parsing to extract dates
                fetched_at=datetime.now(tz=UTC),
                source_metadata={
                    "category": category,
                    "likes": likes,
                    "comments": comments,
                },
                is_processed=False,
            )

        except Exception as e:
            logger.debug(f"Failed to parse post element: {e}")
            return None
