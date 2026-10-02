"""
Order Repository — Database access for orders.
"""

import random
import string
from uuid import UUID

from supabase import Client

from app.database import get_supabase


def _generate_order_number() -> str:
    """
    Generate a human-friendly order number like 'MB-A3X7K2'.

    WHY not just use the UUID?
    UUIDs are great for databases but terrible for humans.
    "Your order MB-A3X7K2" is much easier to read over the phone
    than "your order 550e8400-e29b-41d4-a716-446655440000".
    """
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"MB-{random_part}"


class OrderRepository:
    """Handles all database operations for orders."""

    def __init__(self, db: Client | None = None):
        self.db = db or get_supabase()

    def create_order(self, order_data: dict) -> dict:
        """Create a new order record."""
        order_data["order_number"] = _generate_order_number()
        response = (
            self.db.table("orders")
            .insert(order_data)
            .execute()
        )
        return response.data[0]

    def create_order_items(self, items: list[dict]) -> list[dict]:
        """Bulk insert order items."""
        response = (
            self.db.table("order_items")
            .insert(items)
            .execute()
        )
        return response.data

    def create_shipping_address(self, address_data: dict) -> dict:
        """Save the shipping address snapshot for an order."""
        response = (
            self.db.table("shipping_addresses")
            .insert(address_data)
            .execute()
        )
        return response.data[0]

    def get_order_by_id(self, order_id: UUID) -> dict | None:
        """Fetch a single order with its items and shipping address."""
        response = (
            self.db.table("orders")
            .select(
                "*, order_items(*, books(title, cover_image_url)), "
                "shipping_addresses(*)"
            )
            .eq("id", str(order_id))
            .single()
            .execute()
        )
        return response.data

    def get_order_by_reference(self, payment_reference: str) -> dict | None:
        """Find an order by its Paystack payment reference."""
        response = (
            self.db.table("orders")
            .select("*")
            .eq("payment_reference", payment_reference)
            .maybe_single()
            .execute()
        )
        return response.data

    def get_user_orders(self, user_id: UUID) -> list[dict]:
        """Fetch all orders for a user, newest first."""
        response = (
            self.db.table("orders")
            .select(
                "*, order_items(*, books(title, cover_image_url))"
            )
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    def update_order_status(
        self,
        order_id: UUID,
        status: str,
        payment_status: str,
    ) -> dict:
        """Update order and payment status after payment verification."""
        response = (
            self.db.table("orders")
            .update({
                "status": status,
                "payment_status": payment_status,
            })
            .eq("id", str(order_id))
            .execute()
        )
        return response.data[0]
