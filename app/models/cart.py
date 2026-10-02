"""
Cart-related Pydantic schemas.

The cart is the bridge between browsing and buying. It needs to handle:
1. Logged-in users (cart saved in database)
2. Guests (cart in localStorage, synced on login)
"""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    """Schema for adding an item to the cart."""

    book_id: UUID
    quantity: int = Field(default=1, ge=1, le=99)


class CartItemUpdate(BaseModel):
    """Schema for updating item quantity in the cart."""

    quantity: int = Field(ge=0, le=99)  # 0 means remove


class CartItemResponse(BaseModel):
    """Single cart item with book details for display."""

    id: UUID
    book_id: UUID
    title: str
    cover_image_url: str | None = None
    unit_price: Decimal
    quantity: int
    stock_quantity: int
    line_total: Decimal


class CartResponse(BaseModel):
    """Full cart with all items and totals."""

    id: UUID
    items: list[CartItemResponse] = []
    item_count: int = 0
    subtotal: Decimal = Decimal("0.00")


class CartSyncRequest(BaseModel):
    """
    Sync guest cart items when user logs in.

    When a guest adds books to cart (stored in localStorage) and then
    logs in, we need to merge those items into their database cart.
    """

    items: list[CartItemCreate]
