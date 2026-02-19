"""
Utility functions for the API.
"""


def escape_like_pattern(value: str) -> str:
    """
    Escape special characters in a LIKE pattern to prevent SQL injection.

    The characters %, _, and \\ have special meaning in SQL LIKE patterns:
    - % matches any sequence of characters
    - _ matches any single character
    - \\ is the escape character

    This function escapes them so they are treated as literals.

    Args:
        value: The user input to escape

    Returns:
        Escaped string safe for use in LIKE patterns
    """
    # Escape backslash first (since it's the escape character)
    escaped = value.replace("\\", "\\\\")
    # Then escape % and _
    escaped = escaped.replace("%", "\\%")
    escaped = escaped.replace("_", "\\_")
    return escaped
