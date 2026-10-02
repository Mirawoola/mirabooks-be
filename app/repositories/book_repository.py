"""
Book Repository — Database access for books and categories.

REPOSITORY PATTERN (Like You're 5):
Instead of every part of the app reaching into the database directly
(like kids grabbing toys from a messy box), the repository is a
librarian. You tell the librarian what you want, and they find it for
you. This keeps the database queries in ONE place, making them easy
to find, fix, and test.
"""

from uuid import UUID

from supabase import Client

from app.database import get_supabase


class BookRepository:
    """Handles all database operations for books."""

    def __init__(self, db: Client | None = None):
        self.db = db or get_supabase()

    def get_books(
        self,
        category_slug: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        book_format: str | None = None,
        in_stock: bool | None = None,
        sort_by: str = "newest",
        search: str | None = None,
        page: int = 1,
        page_size: int = 12,
    ) -> tuple[list[dict], int]:
        """
        Fetch a paginated, filtered, and sorted list of books.

        Returns a tuple of (books_list, total_count).
        """
        select_cols = "*, categories(name, slug), book_authors(authors(id, name))"
        if category_slug:
            select_cols = "*, categories!inner(name, slug), book_authors(authors(id, name))"
            
        query = self.db.table("books").select(
            select_cols,
            count="exact",
        )

        # Apply filters
        if category_slug:
            query = query.eq("categories.slug", category_slug)

        if min_price is not None:
            query = query.gte("price", min_price)

        if max_price is not None:
            query = query.lte("price", max_price)

        if book_format:
            query = query.eq("format", book_format)

        if in_stock is True:
            query = query.gt("stock_quantity", 0)

        if search:
            query = query.or_(
                f"title.ilike.%{search}%,"
                f"isbn.ilike.%{search}%,"
                f"description.ilike.%{search}%,"
                f"publisher.ilike.%{search}%"
            )

        # Apply sorting
        sort_map = {
            "newest": ("created_at", {"ascending": False}),
            "price_asc": ("price", {"ascending": True}),
            "price_desc": ("price", {"ascending": False}),
            "popularity": ("is_bestseller", {"ascending": False}),
        }
        sort_column, sort_opts = sort_map.get(
            sort_by, ("created_at", {"ascending": False})
        )
        query = query.order(sort_column, **sort_opts)

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)

        response = query.execute()
        total = response.count if response.count is not None else 0
        return response.data or [], total

    def get_book_by_slug(self, slug: str) -> dict | None:
        """Fetch a single book by its URL-friendly slug."""
        response = (
            self.db.table("books")
            .select("*, categories(*), book_authors(authors(*))")
            .eq("slug", slug)
            .single()
            .execute()
        )
        return response.data

    def get_book_by_id(self, book_id: UUID) -> dict | None:
        """Fetch a single book by its primary key."""
        response = (
            self.db.table("books")
            .select("*, categories(*), book_authors(authors(*))")
            .eq("id", str(book_id))
            .single()
            .execute()
        )
        return response.data

    def get_featured_books(self, limit: int = 8) -> list[dict]:
        """Fetch books marked as featured for the homepage."""
        response = (
            self.db.table("books")
            .select("*, book_authors(authors(id, name))")
            .eq("is_featured", True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def get_bestsellers(self, limit: int = 8) -> list[dict]:
        """Fetch books marked as bestsellers."""
        response = (
            self.db.table("books")
            .select("*, book_authors(authors(id, name))")
            .eq("is_bestseller", True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def get_new_arrivals(self, limit: int = 8) -> list[dict]:
        """Fetch the most recently added books."""
        response = (
            self.db.table("books")
            .select("*, book_authors(authors(id, name))")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def update_stock(self, book_id: UUID, quantity_change: int) -> None:
        """
        Decrease stock after a purchase.

        Uses a negative quantity_change (e.g., -2 means sold 2 copies).
        """
        book = self.get_book_by_id(book_id)
        if book:
            new_quantity = max(0, book["stock_quantity"] + quantity_change)
            self.db.table("books").update(
                {"stock_quantity": new_quantity}
            ).eq("id", str(book_id)).execute()


class CategoryRepository:
    """Handles all database operations for categories."""

    def __init__(self, db: Client | None = None):
        self.db = db or get_supabase()

    def get_all_categories(self) -> list[dict]:
        """Fetch all categories ordered by display_order."""
        response = (
            self.db.table("categories")
            .select("*")
            .order("display_order")
            .execute()
        )
        return response.data or []

    def get_category_by_slug(self, slug: str) -> dict | None:
        """Fetch a single category by slug."""
        response = (
            self.db.table("categories")
            .select("*")
            .eq("slug", slug)
            .single()
            .execute()
        )
        return response.data
