"""
Mirabooks — FastAPI Application Entry Point.

This is the "front door" of the backend. It:
1. Creates the FastAPI app
2. Configures CORS (so the React frontend can talk to us)
3. Registers all route handlers
4. Provides a health check endpoint

CORS (Like You're 5):
By default, a website at localhost:5173 (React) can't talk to
a server at localhost:8000 (FastAPI) — it's a security rule.
CORS is like giving the React app a special pass that says
"Yes, this website is allowed to talk to me."
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, books, cart, categories, checkout

app = FastAPI(
    title="Mirabooks API",
    description=(
        "Backend API for the **Mirabooks** online bookstore.\n\n"
        "## Features\n"
        "- 📚 Browse, search, and filter books by category, author, and price\n"
        "- 🔐 Google OAuth 2.0 authentication\n"
        "- 🛒 Shopping cart with persistent server-side storage\n"
        "- 💳 Paystack payment integration\n"
        "- 📧 Order confirmation emails via Mailgun SMTP\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Mirabooks Support",
        "email": "oladimejimirawoola@gmail.com",
    },
    openapi_tags=[
        {"name": "Health", "description": "Server health checks"},
        {"name": "Auth", "description": "Google OAuth login, token refresh, and user profile"},
        {"name": "Books", "description": "Browse, search, and filter the book catalog"},
        {"name": "Categories", "description": "Book categories and filtering"},
        {"name": "Cart", "description": "Shopping cart management (add, update, remove items)"},
        {"name": "Checkout", "description": "Order placement, payment, and verification"},
    ],
)

# --- CORS Middleware ---
# Allow the React frontend to make requests to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,  # React dev server or production URL
        "https://mirabooks-be.onrender.com",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register Routers ---
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(categories.router)
app.include_router(cart.router)
app.include_router(checkout.router)


# --- Health Check ---
@app.get("/", tags=["Health"])
async def health_check():
    """Basic health check to verify the API is running."""
    return {
        "status": "healthy",
        "app": "Mirabooks API",
        "version": "1.0.0",
    }


@app.get("/api/health", tags=["Health"])
async def api_health():
    """API-prefixed health check for load balancers and monitoring."""
    return {"status": "ok"}
