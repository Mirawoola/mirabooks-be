"""
Books Router — Endpoints for browsing and searching books.

All book endpoints are PUBLIC (no auth required).
Anyone can browse the catalog — you only need to log in to buy.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.models.book import BookFilterParams
from app.services.book_service import BookService

router = APIRouter(prefix="/api/books", tags=["Books"])

book_service = BookService()


@router.get("")
async def list_books(
    category: str | None = Query(None, alias="category"),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    format: str | None = Query(None),
    in_stock: bool | None = Query(None),
    sort_by: str = Query("newest"),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=48),
):
    """
    List books with filtering, sorting, and pagination.

    Query parameters:
    - category: Filter by category slug
    - min_price / max_price: Price range filter
    - format: Book format (Paperback, Hardcover, eBook)
    - in_stock: Only show books with stock > 0
    - sort_by: newest, price_asc, price_desc, popularity
    - search: Text search across title, ISBN, description
    - page / page_size: Pagination
    """
    filters = BookFilterParams(
        category_slug=category,
        min_price=min_price,
        max_price=max_price,
        format=format,
        in_stock=in_stock,
        sort_by=sort_by,
        search=search,
        page=page,
        page_size=page_size,
    )
    return book_service.get_books(filters)


@router.get("/featured")
async def get_featured_books():
    """Fetch books marked as featured (for homepage section)."""
    books = book_service.get_featured_books()
    return {"items": books}


@router.get("/bestsellers")
async def get_bestsellers():
    """Fetch bestseller books (for homepage section)."""
    books = book_service.get_bestsellers()
    return {"items": books}


@router.get("/new-arrivals")
async def get_new_arrivals():
    """Fetch most recently added books (for homepage section)."""
    books = book_service.get_new_arrivals()
    return {"items": books}


@router.get("/search")
async def search_books(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=48),
):
    """
    Search books by title, author, ISBN, or keywords.

    The 'q' parameter is required and must be at least 1 character.
    """
    return book_service.search_books(q, page, page_size)


@router.get("/{slug}")
async def get_book_detail(slug: str):
    """
    Get full details for a single book by its URL slug.

    Example: /api/books/the-great-gatsby
    """
    book = book_service.get_book_detail(slug)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return book
