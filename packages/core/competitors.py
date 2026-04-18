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


def _get_search_pool(domain: str | None) -> set[str]:
    """Get competitor names to search for, filtered by domain if provided."""
    if domain and domain in KNOWN_COMPETITORS:
        return {c.lower() for c in KNOWN_COMPETITORS[domain]}
    return get_all_competitors()


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

    search_pool = _get_search_pool(domain)

    for competitor in search_pool:
        # Use word boundaries to avoid false positives
        # e.g., "mint" shouldn't match "comment" or "minting"
        pattern = rf"\b{re.escape(competitor)}\b"
        if re.search(pattern, text_lower):
            found.append(competitor)

    return list(set(found))
