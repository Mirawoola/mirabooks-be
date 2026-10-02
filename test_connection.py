"""Quick check: do tables exist in Supabase?"""
import httpx

from app.config import settings

SUPABASE_URL = settings.supabase_url
SUPABASE_KEY = settings.supabase_service_role_key

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

for table in ["categories", "authors", "books", "book_authors", "users", "carts", "cart_items", "orders", "order_items", "shipping_addresses"]:
    resp = httpx.get(f"{SUPABASE_URL}/rest/v1/{table}?limit=1", headers=HEADERS, timeout=15.0)
    status = "EXISTS" if resp.status_code == 200 else f"MISSING ({resp.status_code})"
    print(f"  {table}: {status}")
