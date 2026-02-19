"""
API constants.

Centralized constants for pagination, rate limits, and other configuration.
"""

# Pagination defaults
DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 100
MIN_PAGE_LIMIT = 1

# Rate limits (requests per minute)
DEFAULT_RATE_LIMIT = 100
JOBS_RATE_LIMIT = 30
