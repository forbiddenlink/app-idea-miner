"""
API routers package.
"""

from apps.api.app.routers import (
    analytics,
    auth,
    bookmarks,
    clusters,
    export,
    ideas,
    opportunities,
    posts,
    saved_searches,
)

__all__ = [
    "analytics",
    "auth",
    "bookmarks",
    "clusters",
    "export",
    "ideas",
    "opportunities",
    "posts",
    "saved_searches",
]
