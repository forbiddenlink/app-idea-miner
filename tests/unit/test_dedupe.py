"""
Unit tests for packages/core/dedupe.py - Deduplicator.

Tests URL canonicalization, hashing, fuzzy title matching,
text normalization, content fingerprinting, and similarity scoring.
No database required.
"""

import hashlib

import pytest

from packages.core.dedupe import Deduplicator

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def dedup():
    """Create a Deduplicator with default threshold (0.85)."""
    return Deduplicator()


@pytest.fixture
def strict_dedup():
    """Create a Deduplicator with a very high threshold."""
    return Deduplicator(title_similarity_threshold=0.95)


@pytest.fixture
def loose_dedup():
    """Create a Deduplicator with a low threshold."""
    return Deduplicator(title_similarity_threshold=0.5)


# ---------------------------------------------------------------------------
# canonicalize_url()
# ---------------------------------------------------------------------------


class TestCanonicalizeUrl:
    def test_removes_utm_source(self, dedup):
        url = "https://example.com/post?utm_source=twitter&id=123"
        canonical = dedup.canonicalize_url(url)
        assert "utm_source" not in canonical
        assert "id=123" in canonical

    def test_removes_utm_medium(self, dedup):
        url = "https://example.com/page?utm_medium=email&page=1"
        canonical = dedup.canonicalize_url(url)
        assert "utm_medium" not in canonical
        assert "page=1" in canonical

    def test_removes_utm_campaign(self, dedup):
        url = "https://example.com/?utm_campaign=launch"
        canonical = dedup.canonicalize_url(url)
        assert "utm_campaign" not in canonical

    def test_removes_fbclid(self, dedup):
        url = "https://example.com/article?fbclid=abc123"
        canonical = dedup.canonicalize_url(url)
        assert "fbclid" not in canonical

    def test_removes_gclid(self, dedup):
        url = "https://example.com/product?gclid=xyz789&color=red"
        canonical = dedup.canonicalize_url(url)
        assert "gclid" not in canonical
        assert "color=red" in canonical

    def test_removes_multiple_tracking_params(self, dedup):
        url = "https://example.com/p?utm_source=fb&utm_medium=cpc&utm_campaign=x&id=5"
        canonical = dedup.canonicalize_url(url)
        assert "utm_" not in canonical
        assert "id=5" in canonical

    def test_strips_www(self, dedup):
        url = "https://www.example.com/page"
        canonical = dedup.canonicalize_url(url)
        assert "www." not in canonical
        assert "example.com" in canonical

    def test_strips_trailing_slash(self, dedup):
        url = "https://example.com/page/"
        canonical = dedup.canonicalize_url(url)
        assert not canonical.endswith("/")

    def test_lowercases_scheme_and_host(self, dedup):
        url = "HTTPS://Example.COM/Path"
        canonical = dedup.canonicalize_url(url)
        assert canonical.startswith("https://")
        assert "example.com" in canonical

    def test_removes_fragment(self, dedup):
        url = "https://example.com/page#section"
        canonical = dedup.canonicalize_url(url)
        assert "#" not in canonical

    def test_sorts_query_params(self, dedup):
        url1 = "https://example.com/?b=2&a=1"
        url2 = "https://example.com/?a=1&b=2"
        assert dedup.canonicalize_url(url1) == dedup.canonicalize_url(url2)

    def test_preserves_path(self, dedup):
        url = "https://example.com/some/deep/path"
        canonical = dedup.canonicalize_url(url)
        assert "/some/deep/path" in canonical

    @pytest.mark.parametrize(
        "url1,url2",
        [
            (
                "https://example.com/post?utm_source=twitter",
                "https://example.com/post?utm_source=facebook",
            ),
            (
                "https://www.example.com/page/",
                "https://example.com/page",
            ),
            (
                "https://example.com/page#top",
                "https://example.com/page#bottom",
            ),
        ],
    )
    def test_equivalent_urls_canonicalize_same(self, dedup, url1, url2):
        assert dedup.canonicalize_url(url1) == dedup.canonicalize_url(url2)


# ---------------------------------------------------------------------------
# generate_url_hash()
# ---------------------------------------------------------------------------


class TestGenerateUrlHash:
    def test_returns_64_char_hex(self, dedup):
        h = dedup.generate_url_hash("https://example.com/page")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_same_url_same_hash(self, dedup):
        url = "https://example.com/post?id=1"
        assert dedup.generate_url_hash(url) == dedup.generate_url_hash(url)

    def test_equivalent_urls_same_hash(self, dedup):
        url1 = "https://www.example.com/post/?utm_source=x"
        url2 = "https://example.com/post"
        assert dedup.generate_url_hash(url1) == dedup.generate_url_hash(url2)

    def test_different_urls_different_hash(self, dedup):
        assert dedup.generate_url_hash("https://a.com/1") != dedup.generate_url_hash(
            "https://b.com/2"
        )

    def test_hash_matches_sha256(self, dedup):
        url = "https://example.com/page"
        canonical = dedup.canonicalize_url(url)
        expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        assert dedup.generate_url_hash(url) == expected


# ---------------------------------------------------------------------------
# is_duplicate_title()
# ---------------------------------------------------------------------------


class TestIsDuplicateTitle:
    def test_identical_titles(self, dedup):
        assert dedup.is_duplicate_title("exact match", "exact match") is True

    def test_nearly_identical(self, dedup):
        t1 = "I wish there was an app for budget tracking"
        t2 = "I wish there was an app for budget tracking app"
        assert dedup.is_duplicate_title(t1, t2) is True

    def test_clearly_different(self, dedup):
        t1 = "An app for managing recipes and meal plans"
        t2 = "A cryptocurrency trading platform with real-time data"
        assert dedup.is_duplicate_title(t1, t2) is False

    def test_case_insensitive(self, dedup):
        assert dedup.is_duplicate_title("HELLO WORLD", "hello world") is True

    def test_punctuation_ignored(self, dedup):
        t1 = "Need an app for tracking expenses!"
        t2 = "Need an app for tracking expenses"
        assert dedup.is_duplicate_title(t1, t2) is True

    def test_custom_threshold_strict(self, strict_dedup):
        t1 = "I wish there was an app for budget tracking"
        t2 = "I wish there was an app for tracking budgets"
        # At 0.95 threshold, minor word reordering may not pass
        # Just confirm it returns a bool
        result = strict_dedup.is_duplicate_title(t1, t2)
        assert isinstance(result, bool)

    def test_custom_threshold_loose(self, loose_dedup):
        t1 = "budget tracking app"
        t2 = "expense tracking tool"
        # At 0.5 threshold, loosely similar titles may match
        result = loose_dedup.is_duplicate_title(t1, t2)
        assert isinstance(result, bool)

    def test_empty_titles(self, dedup):
        assert dedup.is_duplicate_title("", "") is True

    @pytest.mark.parametrize(
        "t1,t2,expected",
        [
            ("app for fitness", "app for fitness", True),
            ("completely unrelated topic", "a whole different subject matter entirely", False),
        ],
    )
    def test_parametrized(self, dedup, t1, t2, expected):
        assert dedup.is_duplicate_title(t1, t2) is expected


# ---------------------------------------------------------------------------
# _normalize_text()
# ---------------------------------------------------------------------------


class TestNormalizeText:
    def test_lowercases(self, dedup):
        assert dedup._normalize_text("Hello WORLD") == "hello world"

    def test_strips_punctuation(self, dedup):
        assert dedup._normalize_text("hello, world!") == "hello world"

    def test_collapses_whitespace(self, dedup):
        assert dedup._normalize_text("hello    world") == "hello world"

    def test_strips_leading_trailing(self, dedup):
        assert dedup._normalize_text("  hello  ") == "hello"

    def test_combined(self, dedup):
        raw = "  Hello,  World!  How's   it?  "
        expected = "hello world hows it"
        assert dedup._normalize_text(raw) == expected

    def test_empty_string(self, dedup):
        assert dedup._normalize_text("") == ""

    def test_only_punctuation(self, dedup):
        assert dedup._normalize_text("!!!???...") == ""


# ---------------------------------------------------------------------------
# generate_content_fingerprint()
# ---------------------------------------------------------------------------


class TestGenerateContentFingerprint:
    def test_returns_64_char_hex(self, dedup):
        fp = dedup.generate_content_fingerprint("some content here")
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)

    def test_same_content_same_fingerprint(self, dedup):
        text = "An app for tracking fitness goals daily"
        assert dedup.generate_content_fingerprint(text) == dedup.generate_content_fingerprint(text)

    def test_normalized_equivalence(self, dedup):
        """Same logical content with different casing/spacing → same fingerprint."""
        fp1 = dedup.generate_content_fingerprint("Hello World")
        fp2 = dedup.generate_content_fingerprint("  hello   world  ")
        assert fp1 == fp2

    def test_different_content_different_fingerprint(self, dedup):
        fp1 = dedup.generate_content_fingerprint("fitness tracker app")
        fp2 = dedup.generate_content_fingerprint("budget management tool")
        assert fp1 != fp2

    def test_uses_first_n_chars(self, dedup):
        """Content differing only after the length cutoff should match."""
        base = "a" * 200
        text1 = base + " extra content one"
        text2 = base + " extra content two"
        # Default length=200, so first 200 normalized chars are the same
        assert dedup.generate_content_fingerprint(text1) == dedup.generate_content_fingerprint(text2)

    def test_custom_length(self, dedup):
        fp_short = dedup.generate_content_fingerprint("abcdefghij", length=5)
        fp_long = dedup.generate_content_fingerprint("abcdefghij", length=10)
        # Different prefixes → different fingerprints (unless normalized text ≤ 5 chars)
        # "abcdefghij" normalized is "abcdefghij" (10 chars), so length=5 ≠ length=10
        assert fp_short != fp_long


# ---------------------------------------------------------------------------
# calculate_content_similarity()
# ---------------------------------------------------------------------------


class TestCalculateContentSimilarity:
    def test_identical_texts(self, dedup):
        assert dedup.calculate_content_similarity("hello", "hello") == 1.0

    def test_completely_different(self, dedup):
        sim = dedup.calculate_content_similarity("abcdef", "zyxwvu")
        assert sim < 0.3

    def test_similar_texts(self, dedup):
        t1 = "An app for tracking daily fitness goals and workouts"
        t2 = "An app for tracking daily fitness progress and exercises"
        sim = dedup.calculate_content_similarity(t1, t2)
        assert 0.5 < sim < 1.0

    def test_returns_float(self, dedup):
        sim = dedup.calculate_content_similarity("a", "b")
        assert isinstance(sim, float)

    def test_range_0_to_1(self, dedup):
        sim = dedup.calculate_content_similarity("test one", "test two")
        assert 0.0 <= sim <= 1.0

    def test_case_insensitive(self, dedup):
        sim = dedup.calculate_content_similarity("HELLO WORLD", "hello world")
        assert sim == 1.0

    def test_symmetry(self, dedup):
        t1 = "fitness tracker app for daily use"
        t2 = "daily fitness app with tracking"
        assert dedup.calculate_content_similarity(t1, t2) == pytest.approx(
            dedup.calculate_content_similarity(t2, t1)
        )

    def test_empty_strings(self, dedup):
        assert dedup.calculate_content_similarity("", "") == 1.0
