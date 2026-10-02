"""
Common Pydantic schemas shared across models.

WHY shared schemas?
Instead of writing the same "pagination" or "response wrapper" in every
file, we define them once here. DRY = Don't Repeat Yourself.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TimestampMixin(BaseModel):
    """Adds created_at and updated_at to any model that inherits it."""

    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaginationParams(BaseModel):
    """Standard pagination parameters for list endpoints."""

    page: int = 1
    page_size: int = 12

    @property
    def offset(self) -> int:
        """Calculate the database offset from page number."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Wrapper for paginated list responses."""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    """Simple message response for confirmations or errors."""

    message: str
    success: bool = True
