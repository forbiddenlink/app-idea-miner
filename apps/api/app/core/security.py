"""
Security dependencies for the API.
Handles API Key validation.
"""

import secrets

from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from apps.api.app.config import get_settings

# Define the API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

settings = get_settings()


async def get_api_key(api_key_header: str = Security(api_key_header)):
    """
    Validate the API Key provided in the X-API-Key header.

    Args:
        api_key_header: The API Key from the request header.

    Returns:
        The validated API Key.

    Raises:
        HTTPException: If the API Key is missing or invalid.
    """
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials: Missing API Key",
        )

    # Use timing-safe comparison to prevent timing attacks
    if not secrets.compare_digest(api_key_header, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials: Invalid API Key",
        )

    return api_key_header
