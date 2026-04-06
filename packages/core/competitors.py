"""
Competitor detection and tracking for app ideas.

Identifies when users mention existing products alongside their pain points,
indicating market gaps and competitive opportunities.
"""

import logging
import os
import re

logger = logging.getLogger(__name__)

# Known competitors by domain
# Can be extended via environment variable COMPETITOR_LIST_EXTRA
KNOWN_COMPETITORS: dict[str, list[str]] = {
    "productivity": [
        "notion",
        "todoist",
        "asana",
        "monday",
        "clickup",
        "trello",
        "airtable",
        "basecamp",
        "jira",
        "linear",
        "obsidian",
        "roam",
        "evernote",
        "onenote",
        "bear",
        "craft",
        "coda",
        "fibery",
        "height",
        "taskade",
        "tana",
        "capacities",
    ],
    "finance": [
        "mint",
        "ynab",
        "quicken",
        "personal capital",
        "copilot",
        "monarch",
        "simplifi",
        "honeydue",
        "goodbudget",
        "pocketguard",
        "robinhood",
        "acorns",
        "wealthfront",
        "betterment",
        "coinbase",
        "venmo",
        "cashapp",
        "paypal",
        "zelle",
        "stripe",
        "square",
    ],
    "health": [
        "myfitnesspal",
        "noom",
        "headspace",
        "calm",
        "fitbit",
        "strava",
        "peloton",
        "apple health",
        "google fit",
        "whoop",
        "oura",
        "eight sleep",
        "sleep cycle",
        "lifesum",
        "lose it",
        "cronometer",
        "macrofactor",
        "fastic",
        "zero",
        "levels",
    ],
    "communication": [
        "slack",
        "discord",
        "teams",
        "zoom",
        "meet",
        "webex",
        "telegram",
        "whatsapp",
        "signal",
        "imessage",
        "messenger",
        "loom",
        "vidyard",
        "mmhmm",
        "around",
        "gather",
        "butter",
    ],
    "notes": [
        "notion",
        "obsidian",
        "roam",
        "logseq",
        "remnote",
        "mem",
        "reflect",
        "tana",
        "heptabase",
        "scrintal",
        "apple notes",
        "google keep",
        "simplenote",
        "ulysses",
        "ia writer",
    ],
    "email": [
        "gmail",
        "outlook",
        "superhuman",
        "hey",
        "spark",
        "airmail",
        "mailspring",
        "newton",
        "front",
        "missive",
        "shortwave",
        "protonmail",
        "fastmail",
        "zoho mail",
    ],
    "design": [
        "figma",
        "sketch",
        "adobe xd",
        "invision",
        "canva",
        "framer",
        "principle",
        "protopie",
        "marvel",
        "zeplin",
        "miro",
        "figjam",
        "lucidchart",
        "whimsical",
        "excalidraw",
    ],
    "dev_tools": [
        "github",
        "gitlab",
        "bitbucket",
        "vercel",
        "netlify",
        "heroku",
        "railway",
        "fly.io",
        "render",
        "digitalocean",
        "aws",
        "gcp",
        "azure",
        "supabase",
        "firebase",
        "planetscale",
        "vscode",
        "cursor",
        "neovim",
        "jetbrains",
        "replit",
        "codepen",
    ],
    "social": [
        "twitter",
        "x.com",
        "instagram",
        "tiktok",
        "youtube",
        "linkedin",
        "facebook",
        "reddit",
        "threads",
        "mastodon",
        "bluesky",
        "hive",
        "snapchat",
        "pinterest",
        "tumblr",
    ],
    "education": [
        "coursera",
        "udemy",
        "skillshare",
        "masterclass",
        "duolingo",
        "khan academy",
        "brilliant",
        "codecademy",
        "treehouse",
        "pluralsight",
        "oreilly",
        "linkedin learning",
        "edx",
        "anki",
    ],
    "entertainment": [
        "netflix",
        "spotify",
        "youtube",
        "twitch",
        "disney+",
        "hulu",
        "hbo max",
        "amazon prime",
        "apple tv+",
        "paramount+",
        "plex",
        "jellyfin",
        "audible",
        "kindle",
        "pocket casts",
    ],
    "travel": [
        "airbnb",
        "booking.com",
        "expedia",
        "kayak",
        "google flights",
        "skyscanner",
        "hopper",
        "tripadvisor",
        "yelp",
        "google maps",
        "waze",
        "rome2rio",
        "flighty",
        "tripIt",
        "wanderlog",
    ],
    "shopping": [
        "amazon",
        "ebay",
        "etsy",
        "shopify",
        "stripe",
        "afterpay",
        "klarna",
        "honey",
        "rakuten",
        "camelcamelcamel",
        "keepa",
        "fakespot",
        "capital one shopping",
    ],
    "ai_tools": [
        "chatgpt",
        "claude",
        "gemini",
        "perplexity",
        "copilot",
        "midjourney",
        "dalle",
        "stable diffusion",
        "runway",
        "jasper",
        "copy.ai",
        "grammarly",
        "notion ai",
        "otter.ai",
        "descript",
        "elevenlabs",
        "synthesia",
        "heygen",
    ],
}

# Flatten all competitors for quick lookup
_ALL_COMPETITORS: set[str] = set()
for competitors in KNOWN_COMPETITORS.values():
    _ALL_COMPETITORS.update(c.lower() for c in competitors)


def get_all_competitors() -> set[str]:
    """
    Get all known competitor names (lowercase).

    Includes any extra competitors from COMPETITOR_LIST_EXTRA env var.

    Returns:
        Set of competitor names (lowercase)
    """
    competitors = _ALL_COMPETITORS.copy()

    # Add any extra competitors from environment
    extra = os.getenv("COMPETITOR_LIST_EXTRA", "")
    if extra:
        for name in extra.split(","):
            name = name.strip().lower()
            if name:
                competitors.add(name)

    return competitors


def extract_competitors(text: str, domain: str | None = None) -> list[str]:
    """
    Extract competitor mentions from text.

    Args:
        text: Text to analyze
        domain: Optional domain to limit search (productivity, health, etc.)

    Returns:
        List of competitor names found (deduplicated, lowercase)
    """
    text_lower = text.lower()
    found = []

    # Determine which competitors to look for
    if domain and domain in KNOWN_COMPETITORS:
        # Search domain-specific competitors
        search_pool = {c.lower() for c in KNOWN_COMPETITORS[domain]}
    else:
        # Search all competitors
        search_pool = get_all_competitors()

    # Word boundary pattern for accurate matching
    for competitor in search_pool:
        # Use word boundaries to avoid false positives
        # e.g., "mint" shouldn't match "comment" or "minting"
        pattern = rf"\b{re.escape(competitor)}\b"
        if re.search(pattern, text_lower):
            found.append(competitor)

    return list(set(found))


def extract_competitors_with_context(
    text: str, domain: str | None = None
) -> list[dict]:
    """
    Extract competitor mentions with surrounding context.

    Useful for understanding how the competitor is being discussed
    (positive, negative, comparison, etc.)

    Args:
        text: Text to analyze
        domain: Optional domain filter

    Returns:
        List of dicts with 'competitor', 'context', 'sentiment_hint' keys
    """
    results = []
    text_lower = text.lower()

    # Determine search pool
    if domain and domain in KNOWN_COMPETITORS:
        search_pool = {c.lower() for c in KNOWN_COMPETITORS[domain]}
    else:
        search_pool = get_all_competitors()

    # Sentiment indicators
    negative_indicators = [
        "hate",
        "frustrated",
        "annoying",
        "wish",
        "unlike",
        "better than",
        "instead of",
        "switching from",
        "leaving",
        "left",
        "quit",
        "doesn't",
        "can't",
        "won't",
        "missing",
        "lacks",
        "problem with",
    ]
    positive_indicators = [
        "love",
        "great",
        "amazing",
        "best",
        "perfect",
        "like",
        "recommend",
        "use",
        "using",
        "fan of",
        "works well",
    ]

    for competitor in search_pool:
        pattern = rf"\b{re.escape(competitor)}\b"
        for match in re.finditer(pattern, text_lower):
            # Extract context (100 chars before and after)
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end].strip()

            # Determine sentiment hint
            context_lower = context.lower()
            sentiment_hint = "neutral"

            if any(neg in context_lower for neg in negative_indicators):
                sentiment_hint = "negative"
            elif any(pos in context_lower for pos in positive_indicators):
                sentiment_hint = "positive"

            results.append(
                {
                    "competitor": competitor,
                    "context": context,
                    "sentiment_hint": sentiment_hint,
                }
            )

    # Deduplicate by competitor name
    seen = set()
    deduplicated = []
    for result in results:
        if result["competitor"] not in seen:
            seen.add(result["competitor"])
            deduplicated.append(result)

    return deduplicated


def get_domain_for_competitor(competitor: str) -> str | None:
    """
    Find the domain category for a given competitor.

    Args:
        competitor: Competitor name

    Returns:
        Domain name or None if not found
    """
    competitor_lower = competitor.lower()

    for domain, competitors in KNOWN_COMPETITORS.items():
        if competitor_lower in [c.lower() for c in competitors]:
            return domain

    return None


def get_competitor_stats(competitors_list: list[str]) -> dict:
    """
    Get aggregate statistics about competitor mentions.

    Args:
        competitors_list: List of competitor names

    Returns:
        Dict with counts by domain and total
    """
    by_domain: dict[str, int] = {}
    unknown_count = 0

    for competitor in competitors_list:
        domain = get_domain_for_competitor(competitor)
        if domain:
            by_domain[domain] = by_domain.get(domain, 0) + 1
        else:
            unknown_count += 1

    return {
        "total": len(competitors_list),
        "by_domain": by_domain,
        "unknown": unknown_count,
        "unique": list(set(competitors_list)),
    }
