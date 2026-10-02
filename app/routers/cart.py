"""
Cart Router — Endpoints for shopping cart management.

All cart endpoints require authentication (logged-in users).
Guest carts are handled entirely on the frontend (localStorage)
and synced to the database when the user logs in.
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.middleware.auth import require_auth
from app.models.cart import CartItemCreate, CartItemUpdate, CartSyncRequest
from app.services.cart_service import CartService

router = APIRouter(prefix="/api/cart", tags=["Cart"])

cart_service = CartService()


@router.get("")
async def get_cart(current_user: dict = Depends(require_auth)):
    """Get the current user's cart with all items and totals."""
    return cart_service.get_cart(current_user["sub"])


@router.post("/items")
async def add_to_cart(
    item: CartItemCreate,
    current_user: dict = Depends(require_auth),
):
    """
    Add a book to the cart.

    If the book is already in the cart, its quantity is updated
    (upsert behavior via the database constraint).
    """
    return cart_service.add_to_cart(
        current_user["sub"],
        item.book_id,
        item.quantity,
    )


@router.patch("/items/{item_id}")
async def update_cart_item(
    item_id: UUID,
    update: CartItemUpdate,
    current_user: dict = Depends(require_auth),
):
    """
    Update the quantity of a cart item.

    Setting quantity to 0 removes the item entirely.
    """
    return cart_service.update_cart_item(
        current_user["sub"],
        item_id,
        update.quantity,
    )


@router.delete("/items/{item_id}")
async def remove_cart_item(
    item_id: UUID,
    current_user: dict = Depends(require_auth),
):
    """Remove an item from the cart."""
    return cart_service.remove_cart_item(current_user["sub"], item_id)


@router.post("/sync")
async def sync_guest_cart(
    sync_data: CartSyncRequest,
    current_user: dict = Depends(require_auth),
):
    """
    Sync guest cart items to the user's database cart.

    Called immediately after login when the user had items
    in their localStorage cart as a guest.
    """
    guest_items = [item.model_dump() for item in sync_data.items]
    return cart_service.sync_guest_cart(current_user["sub"], guest_items)
