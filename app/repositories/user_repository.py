"""
User Repository — Database access for users and addresses.
"""

from uuid import UUID

from app.database import SupabaseClient, get_supabase


class UserRepository:
    """Handles all database operations for users."""

    def __init__(self, db: SupabaseClient | None = None):
        self.db = db or get_supabase()

    def get_user_by_email(self, email: str) -> dict | None:
        """Find a user by their email address."""
        response = (
            self.db.table("users")
            .select("*")
            .eq("email", email)
            .maybe_single()
            .execute()
        )
        return response.data

    def get_user_by_id(self, user_id: UUID) -> dict | None:
        """Find a user by their primary key."""
        response = (
            self.db.table("users")
            .select("*")
            .eq("id", str(user_id))
            .single()
            .execute()
        )
        return response.data

    def create_user(self, user_data: dict) -> dict:
        """Create a new user record from Google OAuth data."""
        response = (
            self.db.table("users")
            .insert(user_data)
            .execute()
        )
        return response.data[0]

    def update_user(self, user_id: UUID, update_data: dict) -> dict:
        """Update an existing user's profile."""
        response = (
            self.db.table("users")
            .update(update_data)
            .eq("id", str(user_id))
            .execute()
        )
        return response.data[0]

    def get_user_addresses(self, user_id: UUID) -> list[dict]:
        """Fetch all saved addresses for a user."""
        response = (
            self.db.table("addresses")
            .select("*")
            .eq("user_id", str(user_id))
            .order("is_default", desc=True)
            .execute()
        )
        return response.data or []

    def create_address(self, user_id: UUID, address_data: dict) -> dict:
        """Save a new address for a user."""
        address_data["user_id"] = str(user_id)
        response = (
            self.db.table("addresses")
            .insert(address_data)
            .execute()
        )
        return response.data[0]
