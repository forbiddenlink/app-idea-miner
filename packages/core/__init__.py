"""Core utilities for App-Idea Miner."""

import os


def env_is_truthy(name: str) -> bool:
    """Check if an environment variable is set to a truthy value (1, true, yes)."""
    return os.getenv(name, "").lower() in ("1", "true", "yes")
