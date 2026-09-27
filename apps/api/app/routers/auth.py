"""
Authentication endpoints: register, login, and current-user.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.auth import (
    clear_auth_cookies,
    create_access_token,
    get_current_user_id,
    get_password_hash,
    set_auth_cookies,
    verify_password,
)
from apps.api.app.core.rate_limit import RateLimiter
from apps.api.app.database import get_db
from packages.core.models import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Auth"])

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool
    is_admin: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    body: RegisterRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(RateLimiter(times=5, seconds=60))],
):
    """
    Register a new user, set the session as an httpOnly cookie, and also
    return it in the response body for non-browser (Bearer-token) callers.
    """
    normalized_email = body.email.lower().strip()
    existing = await db.scalar(select(User).where(User.email == normalized_email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address already registered",
        )
    user = User(
        email=normalized_email,
        hashed_password=get_password_hash(body.password),
    )
    db.add(user)
    await db.flush()
    token = create_access_token({"sub": str(user.id)})
    set_auth_cookies(response, token)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(RateLimiter(times=10, seconds=60))],
):
    """
    Authenticate with email/password, set the session as an httpOnly
    cookie, and also return it in the response body for non-browser
    (Bearer-token) callers.
    """
    normalized_email = body.email.lower().strip()
    user = await db.scalar(select(User).where(User.email == normalized_email))
    if not user or not verify_password(body.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not bool(user.is_active):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    token = create_access_token({"sub": str(user.id)})
    set_auth_cookies(response, token)
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    """
    Clear the session and CSRF cookies. Always succeeds (idempotent) even
    if there was no active cookie session, since a Bearer-token caller has
    nothing here to clear and that's not an error.
    """
    clear_auth_cookies(response)


@router.get("/me", response_model=UserResponse)
async def me(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return the currently authenticated user."""
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
