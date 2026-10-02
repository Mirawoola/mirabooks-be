"""
Book Service — Business logic for books and categories.

SERVICE LAYER (Like You're 5):
The repository is the librarian who finds books on the shelf.
The service is the TEACHER who decides which books to recommend,
how to organize them, and what rules to follow.

The service layer sits between the API routes and the repository:
  Route → Service → Repository → Database
"""

from app.models.book import BookDetail, BookFilterParams, BookSummary
from app.models.common import PaginatedResponse
from app.repositories.book_repository import BookRepository, CategoryRepository


class BookService:
    """Business logic for book operations."""

    def __init__(self):
        self.book_repo = BookRepository()
        self.category_repo = CategoryRepository()

    def _format_book_summary(self, book: dict) -> dict:
        """Transform raw database row into a BookSummary-compatible dict."""
        authors = []
        if book.get("book_authors"):
            for book_author in book["book_authors"]:
                author_data = book_author.get("authors")
                if author_data:
                    authors.append(author_data["name"])

        category_name = None
        if book.get("categories"):
            category_name = book["categories"].get("name")

        return {
            "id": book["id"],
            "title": book["title"],
            "slug": book["slug"],
            "price": book["price"],
            "discount_price": book.get("discount_price"),
            "cover_image_url": book.get("cover_image_url"),
            "authors": authors,
            "category_name": category_name,
            "stock_quantity": book.get("stock_quantity", 0),
            "is_featured": book.get("is_featured", False),
            "is_bestseller": book.get("is_bestseller", False),
        }

    def _format_book_detail(self, book: dict) -> dict:
        """Transform raw database row into a BookDetail-compatible dict."""
        authors = []
        if book.get("book_authors"):
            for book_author in book["book_authors"]:
                author_data = book_author.get("authors")
                if author_data:
                    authors.append(author_data)

        return {
            **book,
            "category": book.get("categories"),
            "authors": authors,
        }

    def get_books(self, filters: BookFilterParams) -> PaginatedResponse:
        """Fetch a paginated list of books with filters applied."""
        books, total = self.book_repo.get_books(
            category_slug=filters.category_slug,
            min_price=float(filters.min_price) if filters.min_price else None,
            max_price=float(filters.max_price) if filters.max_price else None,
            book_format=filters.format,
            in_stock=filters.in_stock,
            sort_by=filters.sort_by,
            search=filters.search,
            page=filters.page,
            page_size=filters.page_size,
        )

        formatted = [self._format_book_summary(book) for book in books]
        total_pages = max(1, -(-total // filters.page_size))  # Ceiling division

        return PaginatedResponse(
            items=formatted,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    def get_book_detail(self, slug: str) -> dict | None:
        """Fetch full details for a single book."""
        book = self.book_repo.get_book_by_slug(slug)
        if not book:
            return None
        return self._format_book_detail(book)

    def get_featured_books(self) -> list[dict]:
        """Fetch featured books for the homepage."""
        books = self.book_repo.get_featured_books()
        return [self._format_book_summary(book) for book in books]

    def get_bestsellers(self) -> list[dict]:
        """Fetch bestseller books."""
        books = self.book_repo.get_bestsellers()
        return [self._format_book_summary(book) for book in books]

    def get_new_arrivals(self) -> list[dict]:
        """Fetch newly added books."""
        books = self.book_repo.get_new_arrivals()
        return [self._format_book_summary(book) for book in books]

    def search_books(self, query: str, page: int = 1, page_size: int = 12) -> PaginatedResponse:
        """Search books by title, author, ISBN, or keywords."""
        filters = BookFilterParams(search=query, page=page, page_size=page_size)
        return self.get_books(filters)

    def get_all_categories(self) -> list[dict]:
        """Fetch all book categories."""
        return self.category_repo.get_all_categories()

    def get_books_by_category(
        self,
        category_slug: str,
        page: int = 1,
        page_size: int = 12,
        sort_by: str = "newest",
    ) -> PaginatedResponse:
        """Fetch books in a specific category."""
        filters = BookFilterParams(
            category_slug=category_slug,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
        )
        return self.get_books(filters)
