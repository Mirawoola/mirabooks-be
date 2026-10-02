"""
User-related Pydantic schemas.

Handles both Google OAuth users and guest checkout users.
We never store passwords — Google handles authentication for us.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """User profile returned in API responses."""

    id: UUID
    email: str
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    auth_provider: str = "google"
    created_at: datetime | None = None


class GoogleAuthRequest(BaseModel):
    """Payload sent from frontend after Google OAuth flow."""

    credential: str  # The ID token from Google


class AddressCreate(BaseModel):
    """Schema for creating a new saved address."""

    full_name: str
    phone: str
    street: str
    city: str
    state: str
    postal_code: str = ""
    country: str = "Nigeria"
    is_default: bool = False


class AddressResponse(AddressCreate):
    """Saved address returned in API responses."""

    id: UUID
    user_id: UUID
