"""
Cart Repository — Database access for shopping carts.

DESIGN DECISION: One cart per user (enforced by UNIQUE constraint on user_id).
Cart items use a UNIQUE constraint on (cart_id, book_id) — if you add the same
book again, we update the quantity instead of creating a duplicate row.
"""

from uuid import UUID

from app.database import SupabaseClient, get_supabase


class CartRepository:
    """Handles all database operations for carts and cart items."""

    def __init__(self, db: SupabaseClient | None = None):
        self.db = db or get_supabase()

    def get_or_create_cart(self, user_id: UUID) -> dict:
        """
        Get the user's cart, or create one if it doesn't exist.

        This is an idempotent operation — calling it multiple times
        for the same user always returns the same cart.
        """
        existing = (
            self.db.table("carts")
            .select("*")
            .eq("user_id", str(user_id))
            .maybe_single()
            .execute()
        )
        if existing.data:
            return existing.data

        new_cart = (
            self.db.table("carts")
            .insert({"user_id": str(user_id)})
            .execute()
        )
        return new_cart.data[0]

    def get_cart_items(self, cart_id: UUID) -> list[dict]:
        """Fetch all items in a cart with book details."""
        response = (
            self.db.table("cart_items")
            .select("*, books(id, title, cover_image_url, price, stock_quantity)")
            .eq("cart_id", str(cart_id))
            .execute()
        )
        return response.data or []

    def add_item(
        self,
        cart_id: UUID,
        book_id: UUID,
        quantity: int,
        unit_price: float,
    ) -> dict:
        """
        Add a book to the cart.

        Uses upsert with the (cart_id, book_id) constraint —
        if the book is already in the cart, update the quantity.
        """
        response = (
            self.db.table("cart_items")
            .upsert(
                {
                    "cart_id": str(cart_id),
                    "book_id": str(book_id),
                    "quantity": quantity,
                    "unit_price": unit_price,
                },
                on_conflict="cart_id,book_id",
            )
            .execute()
        )
        return response.data[0]

    def update_item_quantity(self, item_id: UUID, quantity: int) -> dict | None:
        """Update the quantity of a specific cart item."""
        if quantity <= 0:
            return self.remove_item(item_id)

        response = (
            self.db.table("cart_items")
            .update({"quantity": quantity})
            .eq("id", str(item_id))
            .execute()
        )
        return response.data[0] if response.data else None

    def remove_item(self, item_id: UUID) -> None:
        """Remove an item from the cart."""
        self.db.table("cart_items").delete().eq("id", str(item_id)).execute()

    def clear_cart(self, cart_id: UUID) -> None:
        """Remove all items from a cart (after checkout)."""
        self.db.table("cart_items").delete().eq("cart_id", str(cart_id)).execute()
