"""
Cart Service — Business logic for shopping cart operations.

BUSINESS RULES:
1. You can't add more items than are in stock
2. Each user has exactly ONE cart (no duplicates)
3. Adding the same book twice updates the quantity
4. Guest carts sync to the database when the user logs in
"""

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status

from app.repositories.book_repository import BookRepository
from app.repositories.cart_repository import CartRepository


class CartService:
    """Business logic for cart operations."""

    def __init__(self):
        self.cart_repo = CartRepository()
        self.book_repo = BookRepository()

    def _format_cart_response(self, cart: dict, items: list[dict]) -> dict:
        """Transform raw cart data into a clean response."""
        formatted_items = []
        subtotal = Decimal("0.00")

        for item in items:
            book = item.get("books", {})
            unit_price = Decimal(str(item["unit_price"]))
            quantity = item["quantity"]
            line_total = unit_price * quantity
            subtotal += line_total

            formatted_items.append({
                "id": item["id"],
                "book_id": item["book_id"],
                "title": book.get("title", "Unknown"),
                "cover_image_url": book.get("cover_image_url"),
                "unit_price": unit_price,
                "quantity": quantity,
                "stock_quantity": book.get("stock_quantity", 0),
                "line_total": line_total,
            })

        return {
            "id": cart["id"],
            "items": formatted_items,
            "item_count": sum(item["quantity"] for item in formatted_items),
            "subtotal": subtotal,
        }

    def get_cart(self, user_id: UUID) -> dict:
        """Get the user's cart with all items and totals."""
        cart = self.cart_repo.get_or_create_cart(user_id)
        items = self.cart_repo.get_cart_items(cart["id"])
        return self._format_cart_response(cart, items)

    def add_to_cart(self, user_id: UUID, book_id: UUID, quantity: int) -> dict:
        """
        Add a book to the user's cart.

        Validates stock availability before adding.
        """
        # Check if book exists and has enough stock
        book = self.book_repo.get_book_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found",
            )

        if book["stock_quantity"] < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {book['stock_quantity']} copies available",
            )

        # Get or create cart, then add item
        cart = self.cart_repo.get_or_create_cart(user_id)
        price = book.get("discount_price") or book["price"]
        self.cart_repo.add_item(cart["id"], book_id, quantity, float(price))

        # Return updated cart
        return self.get_cart(user_id)

    def update_cart_item(
        self,
        user_id: UUID,
        item_id: UUID,
        quantity: int,
    ) -> dict:
        """Update the quantity of an item in the cart."""
        if quantity <= 0:
            self.cart_repo.remove_item(item_id)
        else:
            self.cart_repo.update_item_quantity(item_id, quantity)

        return self.get_cart(user_id)

    def remove_cart_item(self, user_id: UUID, item_id: UUID) -> dict:
        """Remove an item from the cart entirely."""
        self.cart_repo.remove_item(item_id)
        return self.get_cart(user_id)

    def sync_guest_cart(self, user_id: UUID, guest_items: list[dict]) -> dict:
        """
        Merge guest cart items into the user's database cart.

        Called when a guest logs in. For each item:
        - If the book is already in their db cart → keep the higher quantity
        - If not → add it
        """
        for item in guest_items:
            book = self.book_repo.get_book_by_id(item["book_id"])
            if book and book["stock_quantity"] >= item["quantity"]:
                cart = self.cart_repo.get_or_create_cart(user_id)
                price = book.get("discount_price") or book["price"]
                self.cart_repo.add_item(
                    cart["id"],
                    item["book_id"],
                    item["quantity"],
                    float(price),
                )

        return self.get_cart(user_id)
