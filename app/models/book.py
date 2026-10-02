"""
Book-related Pydantic schemas.

These schemas act as contracts between the API and the outside world.
Every piece of data coming IN is validated, and every piece going OUT
has a guaranteed shape. No surprises.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class AuthorResponse(BaseModel):
    """Author data returned in API responses."""

    id: UUID
    name: str
    bio: str | None = None
    image_url: str | None = None


class CategoryResponse(BaseModel):
    """Category data returned in API responses."""

    id: UUID
    name: str
    slug: str
    description: str | None = None
    image_url: str | None = None
    display_order: int = 0


class BookSummary(BaseModel):
    """
    Lightweight book data for list views (grids, search results).

    WHY a separate summary?
    Loading every detail for 50 books at once is wasteful. The grid
    only needs the cover, title, author, and price. We send less data
    over the network = faster page loads.
    """

    id: UUID
    title: str
    slug: str
    price: Decimal
    discount_price: Decimal | None = None
    cover_image_url: str | None = None
    authors: list[str] = []
    category_name: str | None = None
    stock_quantity: int = 0
    is_featured: bool = False
    is_bestseller: bool = False


class BookDetail(BaseModel):
    """Full book data for the detail page."""

    id: UUID
    title: str
    slug: str
    isbn: str | None = None
    price: Decimal
    discount_price: Decimal | None = None
    description: str | None = None
    cover_image_url: str | None = None
    publisher: str | None = None
    publication_date: date | None = None
    pages: int | None = None
    language: str = "English"
    format: str = "Paperback"
    stock_quantity: int = 0
    is_featured: bool = False
    is_bestseller: bool = False
    category: CategoryResponse | None = None
    authors: list[AuthorResponse] = []
    created_at: datetime | None = None


class BookFilterParams(BaseModel):
    """Query parameters for filtering book listings."""

    category_slug: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    format: str | None = None
    in_stock: bool | None = None
    sort_by: str = "newest"  # newest, price_asc, price_desc, popularity
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=12, ge=1, le=48)
