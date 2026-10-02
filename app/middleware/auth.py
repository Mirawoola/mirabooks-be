"""
Authentication Middleware.

This is the "security guard" of our app. It checks every request
to see if the person is who they claim to be.

HOW IT WORKS (Like You're 5):
1. User logs in with Google → gets a special wristband (JWT token)
2. Every time they ask for something, they show their wristband
3. This middleware checks: "Is this wristband real? Is it expired?"
4. If yes → let them in. If no → "Sorry, you can't come in."

We have TWO guards:
- require_auth: MUST have a valid wristband (for cart, orders, etc.)
- optional_auth: It's okay if you don't have one (for browsing books)
"""

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

from app.config import settings
from app.database import get_supabase


def _extract_token(request: Request) -> str | None:
    """Pull the JWT token from the Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header.removeprefix("Bearer ").strip()


def _decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.app_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from err


async def require_auth(request: Request) -> dict:
    """
    Dependency that REQUIRES a valid JWT token.

    Use this for endpoints that need a logged-in user:
    - Cart operations
    - Checkout
    - Order history
    """
    token = _extract_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return _decode_token(token)


async def optional_auth(request: Request) -> dict | None:
    """
    Dependency that OPTIONALLY accepts a JWT token.

    Use this for endpoints that work for everyone but behave
    differently for logged-in users (e.g., showing personalized
    recommendations).
    """
    token = _extract_token(request)
    if not token:
        return None
    try:
        return _decode_token(token)
    except HTTPException:
        return None
