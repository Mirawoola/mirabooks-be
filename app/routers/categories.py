"""
Categories Router — Endpoints for book categories.
"""

from fastapi import APIRouter, Query

from app.services.book_service import BookService

router = APIRouter(prefix="/api/categories", tags=["Categories"])

book_service = BookService()


@router.get("")
async def list_categories():
    """Fetch all book categories for navigation and filtering."""
    categories = book_service.get_all_categories()
    return {"items": categories}


@router.get("/{slug}/books")
async def get_books_by_category(
    slug: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=48),
    sort_by: str = Query("newest"),
):
    """Fetch books belonging to a specific category."""
    return book_service.get_books_by_category(slug, page, page_size, sort_by)
