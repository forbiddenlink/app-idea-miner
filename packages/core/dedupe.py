"""
Deduplication utilities for App-Idea Miner.
Handles URL normalization, hashing, and content similarity detection.
"""

import hashlib
import re
from difflib import SequenceMatcher
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


class Deduplicator:
    """
    Handles deduplication of posts and ideas.
    Uses URL hashing and fuzzy text matching.
    """

    def __init__(self, title_similarity_threshold: float = 0.85):
        """
        Initialize deduplicator.

        Args:
            title_similarity_threshold: Minimum similarity score (0-1) to consider titles duplicates
        """
        self.title_similarity_threshold = title_similarity_threshold

    def canonicalize_url(self, url: str) -> str:
        """
        Normalize URL by removing tracking parameters and standardizing format.

        Args:
            url: Original URL

        Returns:
            Canonicalized URL string

        Example:
            >>> d = Deduplicator()
            >>> d.canonicalize_url('https://example.com/post?utm_source=twitter&id=123')
            'https://example.com/post?id=123'
        """
        # Parse URL
        parsed = urlparse(url)

        # Remove common tracking parameters
        tracking_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
            "mc_eid",
            "mc_cid",
            "_ga",
            "ref",
            "source",
        }

        query_params = parse_qs(parsed.query)
        filtered_params = {
            k: v for k, v in query_params.items() if k not in tracking_params
        }

        # Sort params for consistency
        sorted_query = urlencode(sorted(filtered_params.items()), doseq=True)

        # Normalize scheme and netloc
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower()

        # Remove 'www.' prefix
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # Remove trailing slash from path
        path = parsed.path.rstrip("/")

        # Reconstruct URL
        canonical = urlunparse(
            (
                scheme,
                netloc,
                path,
                parsed.params,
                sorted_query,
                "",  # Remove fragment
            )
        )

        return canonical

    def generate_url_hash(self, url: str) -> str:
        """
        Generate SHA-256 hash of canonicalized URL for fast lookups.

        Args:
            url: Original URL

        Returns:
            64-character hexadecimal hash
        """
        canonical = self.canonicalize_url(url)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def is_duplicate_title(self, title1: str, title2: str) -> bool:
        """
        Check if two titles are duplicates using fuzzy matching.

        Args:
            title1: First title
            title2: Second title

        Returns:
            True if titles are considered duplicates

        Example:
            >>> d = Deduplicator()
            >>> d.is_duplicate_title(
            ...     "I wish there was an app for budget tracking",
            ...     "I wish there was an app for tracking budgets"
            ... )
            True
        """
        # Normalize titles
        norm1 = self._normalize_text(title1)
        norm2 = self._normalize_text(title2)

        # Calculate similarity ratio
        ratio = SequenceMatcher(None, norm1, norm2).ratio()

        return ratio >= self.title_similarity_threshold

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.

        Args:
            text: Original text

        Returns:
            Normalized text (lowercase, no extra spaces)
        """
        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Remove common punctuation
        text = re.sub(r"[^\w\s]", "", text)

        return text

    def generate_content_fingerprint(self, content: str, length: int = 200) -> str:
        """
        Generate a fingerprint of content for similarity detection.
        Uses first N characters after normalization.

        Args:
            content: Content text
            length: Number of characters to include in fingerprint

        Returns:
            SHA-256 hash of normalized content prefix
        """
        normalized = self._normalize_text(content)[:length]
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def calculate_content_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate similarity between two content strings.

        Args:
            content1: First content
            content2: Second content

        Returns:
            Similarity score between 0 and 1
        """
        norm1 = self._normalize_text(content1)
        norm2 = self._normalize_text(content2)

        return SequenceMatcher(None, norm1, norm2).ratio()


# Singleton instance
deduplicator = Deduplicator()


# Convenience functions
def canonicalize_url(url: str) -> str:
    """Canonicalize URL using singleton deduplicator."""
    return deduplicator.canonicalize_url(url)


def generate_url_hash(url: str) -> str:
    """Generate URL hash using singleton deduplicator."""
    return deduplicator.generate_url_hash(url)


def is_duplicate_title(title1: str, title2: str, threshold: float = 0.85) -> bool:
    """Check if titles are duplicates using singleton deduplicator."""
    temp_dedup = Deduplicator(title_similarity_threshold=threshold)
    return temp_dedup.is_duplicate_title(title1, title2)
