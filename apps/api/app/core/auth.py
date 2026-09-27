"""
JWT authentication utilities.
Handles token creation/verification, cookie-based session auth, CSRF, and
password hashing.
"""

import logging
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, Request, Response, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from apps.api.app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme. `auto_error=False` so a request with neither a cookie
# nor an Authorization header falls through to get_current_user_id's own
# 401, rather than FastAPI's security-scheme error, giving one consistent
# error shape regardless of which auth method is missing.
bearer_scheme = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# --- Cookie-based session auth -----------------------------------------
#
# The access token used to live in the frontend's localStorage, which is
# readable by any script running on the page (XSS-exploitable). It now lives
# in an httpOnly cookie the browser attaches automatically and JavaScript
# cannot read. Authorization-header (Bearer) support is KEPT as a fallback:
# checked (README.md "JWT Bearer: Authorization: Bearer <token> (user
# sessions)") and this repo's own test suite (tests/test_api_auth.py and
# others) drives the API purely via Bearer tokens with no browser/cookie
# jar involved. Removing it would break that suite for no security benefit,
# since a non-cookie client was never exposed to the XSS risk this migration
# fixes. The cookie is the primary path for the browser app; Bearer remains
# for direct API callers.
ACCESS_TOKEN_COOKIE_NAME = "aim_access_token"

# Double-submit CSRF cookie: NOT httpOnly (the frontend must be able to read
# it and echo it back), but still Secure + SameSite so it can't be set or
# read cross-site. See verify_csrf_token below and the CSRFMiddleware in
# apps/api/app/main.py for how it's checked.
CSRF_COOKIE_NAME = "aim_csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"

# SameSite=Lax matches this repo's canonical deployment (vercel.json serves
# the API and the frontend from the same Vercel project, i.e. the same
# origin) and is CSRF-resistant by default for that setup. It is NOT
# sufficient if the frontend and API are deployed on different registrable
# domains (the split Railway-API + separately-hosted-frontend layout this
# repo's docs/DEPLOYMENT.md also documents as a supported option) — a
# SameSite=Lax cookie is not sent on cross-site XHR/fetch requests at all,
# only on top-level cross-site GET navigation, so login would silently
# appear to "not stick" on that topology. Fixing that would mean
# SameSite=None (+ Secure), which trades away same-site CSRF protection by
# default and is out of scope for this change; flagged here rather than
# silently shipping a config that only works for one of the two documented
# deployment shapes.
COOKIE_SAMESITE = "lax"


def _cookie_max_age_seconds() -> int:
    return ACCESS_TOKEN_EXPIRE_MINUTES * 60


def set_auth_cookies(response: Response, access_token: str) -> str:
    """
    Set the httpOnly session cookie and a fresh double-submit CSRF cookie.

    Returns the generated CSRF token (callers don't need it, but tests do).
    """
    max_age = _cookie_max_age_seconds()
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        max_age=max_age,
        path="/",
        secure=True,
        httponly=True,
        samesite=COOKIE_SAMESITE,
    )
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age,
        path="/",
        secure=True,
        httponly=False,
        samesite=COOKIE_SAMESITE,
    )
    return csrf_token


def clear_auth_cookies(response: Response) -> None:
    """Clear both auth cookies on logout."""
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE_NAME, path="/")
    response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")


def get_password_hash(password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload to encode (will include 'exp' claim automatically)
        expires_delta: Token lifetime; defaults to ACCESS_TOKEN_EXPIRE_MINUTES

    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.

    Raises:
        HTTPException 401 if token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> str:
    """
    FastAPI dependency: extract and validate the JWT, return the user id.

    Checks the httpOnly session cookie first (the browser app's path), then
    falls back to an Authorization: Bearer header (direct API callers, and
    this repo's own test suite).

    Raises:
        HTTPException 401 if missing or invalid
    """
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if token is None and credentials is not None:
        token = credentials.credentials

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


def verify_csrf_token(request: Request) -> None:
    """
    FastAPI dependency for state-changing routes reached via the cookie
    session: enforce the double-submit CSRF token.

    Only enforced when the request is actually cookie-authenticated (the
    access-token cookie is present) — a Bearer-token API caller has no
    ambient cookie for an attacker's page to ride along on, so there's
    nothing for CSRF to protect there.

    Raises:
        HTTPException 403 if the request is cookie-authenticated and the
        X-CSRF-Token header is missing or doesn't match the CSRF cookie.
    """
    if ACCESS_TOKEN_COOKIE_NAME not in request.cookies:
        return  # Bearer-token caller; no cookie session to forge.

    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get(CSRF_HEADER_NAME)
    if (
        not cookie_token
        or not header_token
        or not secrets.compare_digest(cookie_token, header_token)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid",
        )
