"""
Database Setup — Creates tables and seeds data via Supabase REST API.

Uses httpx to connect to Supabase directly (bypassing supabase-py which
is incompatible with Python 3.14).
"""
import httpx
import uuid
import json

from app.config import settings

SUPABASE_URL = settings.supabase_url
SUPABASE_KEY = settings.supabase_service_role_key

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

client = httpx.Client(base_url=SUPABASE_URL, headers=HEADERS, timeout=30.0)


def upsert(table, data, on_conflict="id"):
    """Insert or update rows in a table."""
    headers = {
        **HEADERS,
        "Prefer": "return=representation,resolution=merge-duplicates",
    }
    resp = httpx.post(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=headers,
        json=data if isinstance(data, list) else [data],
        timeout=30.0,
    )
    if resp.status_code not in (200, 201):
        print(f"  ERROR upserting into {table}: {resp.status_code} {resp.text[:300]}")
        return []
    return resp.json()


def insert_if_not_exists(table, data, unique_col="slug"):
    """Insert data, skip if unique constraint violation."""
    headers = {
        **HEADERS,
        "Prefer": "return=representation",
    }
    results = []
    items = data if isinstance(data, list) else [data]
    for item in items:
        # Check if exists
        check_resp = httpx.get(
            f"{SUPABASE_URL}/rest/v1/{table}?{unique_col}=eq.{item[unique_col]}",
            headers=HEADERS,
            timeout=15.0,
        )
        existing = check_resp.json() if check_resp.status_code == 200 else []
        if existing:
            results.append(existing[0])
            continue

        resp = httpx.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=headers,
            json=item,
            timeout=15.0,
        )
        if resp.status_code in (200, 201):
            results.append(resp.json()[0] if resp.json() else item)
        else:
            print(f"  WARN: Could not insert into {table}: {resp.status_code} {resp.text[:200]}")
    return results


def run():
    print("=" * 60)
    print("  Mirabooks -- Database Setup")
    print("=" * 60)

    # --- Check if tables exist by trying a query ---
    print("\n1. Checking if tables exist...")
    test_resp = httpx.get(
        f"{SUPABASE_URL}/rest/v1/categories?limit=1",
        headers=HEADERS,
        timeout=15.0,
    )
    if test_resp.status_code == 404 or (test_resp.status_code >= 400 and "relation" in test_resp.text.lower()):
        print("   [!] Tables don't exist yet!")
        print("   You need to run the SQL schema in your Supabase Dashboard:")
        print("   Go to: https://supabase.com/dashboard/project/aymbzilbsmwucmdhlfey/sql/new")
        print("   Copy and paste the contents of 'supabase/migrations/001_initial_schema.sql'")
        print("   Then re-run this script.")
        return
    elif test_resp.status_code == 200:
        print("   [OK] Tables exist!")
    else:
        print(f"   Response: {test_resp.status_code} — {test_resp.text[:200]}")
        print("   Continuing anyway...")

    # --- Seed Categories ---
    print("\n2. Seeding categories...")
    categories = [
        {"id": str(uuid.uuid4()), "name": "African Literature", "slug": "african-literature",
         "description": "Classic and contemporary African novels, poetry, and plays.",
         "image_url": "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=300&fit=crop",
         "display_order": 1},
        {"id": str(uuid.uuid4()), "name": "Science Fiction", "slug": "science-fiction",
         "description": "Explore distant galaxies, future technologies, and alternate realities.",
         "image_url": "https://images.unsplash.com/photo-1614729939124-032f0b56c9ce?w=300&fit=crop",
         "display_order": 2},
        {"id": str(uuid.uuid4()), "name": "Business & Tech", "slug": "business-tech",
         "description": "Leadership, startups, innovation, and the future of work.",
         "image_url": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=300&fit=crop",
         "display_order": 3},
        {"id": str(uuid.uuid4()), "name": "Self-Help", "slug": "self-help",
         "description": "Personal growth, productivity, and building better habits.",
         "image_url": "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?w=300&fit=crop",
         "display_order": 4},
        {"id": str(uuid.uuid4()), "name": "Romance", "slug": "romance",
         "description": "Love stories, contemporary romance, and historical fiction.",
         "image_url": "https://images.unsplash.com/photo-1474552226712-ac0f0961a954?w=300&fit=crop",
         "display_order": 5},
        {"id": str(uuid.uuid4()), "name": "Children's Books", "slug": "childrens-books",
         "description": "Picture books, early readers, and middle grade adventures.",
         "image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=300&fit=crop",
         "display_order": 6},
    ]

    cat_results = insert_if_not_exists("categories", categories)
    cat_ids = {c["slug"]: c["id"] for c in cat_results}
    print(f"   [OK] {len(cat_results)} categories ready.")

    # --- Seed Authors ---
    print("\n3. Seeding authors...")
    authors_data = [
        {"id": str(uuid.uuid4()), "name": "Chinua Achebe", "bio": "Nigerian novelist, best known for Things Fall Apart."},
        {"id": str(uuid.uuid4()), "name": "Chimamanda Ngozi Adichie", "bio": "Nigerian writer known for Half of a Yellow Sun and Americanah."},
        {"id": str(uuid.uuid4()), "name": "Ngũgĩ wa Thiong'o", "bio": "Kenyan writer, a leading figure in post-colonial literature."},
        {"id": str(uuid.uuid4()), "name": "Wole Soyinka", "bio": "Nigerian playwright, first African Nobel laureate in Literature."},
        {"id": str(uuid.uuid4()), "name": "Frank Herbert", "bio": "American sci-fi author best known for the Dune series."},
        {"id": str(uuid.uuid4()), "name": "Isaac Asimov", "bio": "Prolific sci-fi author known for Foundation and Robot series."},
        {"id": str(uuid.uuid4()), "name": "James Clear", "bio": "Author focused on habits, decision making, and continuous improvement."},
        {"id": str(uuid.uuid4()), "name": "Peter Thiel", "bio": "Entrepreneur, co-founder of PayPal, author of Zero to One."},
        {"id": str(uuid.uuid4()), "name": "Robert C. Martin", "bio": "Software engineer known as Uncle Bob, expert on clean code."},
        {"id": str(uuid.uuid4()), "name": "Ayọ̀bámi Adébáyọ̀", "bio": "Nigerian author of Stay With Me."},
        {"id": str(uuid.uuid4()), "name": "Buchi Emecheta", "bio": "Nigerian-born British novelist, author of The Joys of Motherhood."},
        {"id": str(uuid.uuid4()), "name": "Nnedi Okofor", "bio": "Nigerian-American writer of science fiction and fantasy."},
        {"id": str(uuid.uuid4()), "name": "Malcolm Gladwell", "bio": "Canadian-born author known for Outliers and Tipping Point."},
        {"id": str(uuid.uuid4()), "name": "Mark Manson", "bio": "American self-help author."},
    ]

    auth_results = insert_if_not_exists("authors", authors_data, unique_col="name")
    author_ids = {a["name"]: a["id"] for a in auth_results}
    print(f"   [OK] {len(auth_results)} authors ready.")

    # --- Seed Books ---
    print("\n4. Seeding books...")
    books_data = [
        # African Literature
        {"title": "Things Fall Apart", "slug": "things-fall-apart", "isbn": "978-0385474542",
         "price": 3500, "discount_price": 2800,
         "description": "A masterpiece of African literature. Okonkwo is a respected leader in the Igbo community of Umuofia, but the arrival of colonial powers disrupts his traditional way of life.",
         "cover_image_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400&fit=crop",
         "publisher": "Anchor Books", "pages": 209, "stock_quantity": 45,
         "is_featured": True, "is_bestseller": True,
         "category_slug": "african-literature", "author_names": ["Chinua Achebe"]},

        {"title": "Half of a Yellow Sun", "slug": "half-of-a-yellow-sun", "isbn": "978-1400095209",
         "price": 4200,
         "description": "Set during the Nigerian Civil War, this powerful novel follows the lives of five characters navigating love, politics, and survival.",
         "cover_image_url": "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400&fit=crop",
         "publisher": "Anchor Books", "pages": 543, "stock_quantity": 30,
         "is_featured": True, "is_bestseller": False,
         "category_slug": "african-literature", "author_names": ["Chimamanda Ngozi Adichie"]},

        {"title": "Americanah", "slug": "americanah", "isbn": "978-0307455925",
         "price": 4500, "discount_price": 3800,
         "description": "A powerful story of love and race centered on a young Nigerian woman's experience in America.",
         "cover_image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400&fit=crop",
         "publisher": "Alfred A. Knopf", "pages": 477, "stock_quantity": 25,
         "is_featured": False, "is_bestseller": True,
         "category_slug": "african-literature", "author_names": ["Chimamanda Ngozi Adichie"]},

        {"title": "A Grain of Wheat", "slug": "a-grain-of-wheat", "isbn": "978-0143106760",
         "price": 3200,
         "description": "Set on the eve of Kenyan independence, this novel explores guilt, sacrifice, and betrayal during the Mau Mau uprising.",
         "cover_image_url": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=400&fit=crop",
         "publisher": "Penguin Books", "pages": 280, "stock_quantity": 18,
         "is_featured": False, "is_bestseller": False,
         "category_slug": "african-literature", "author_names": ["Ngũgĩ wa Thiong'o"]},

        {"title": "Stay With Me", "slug": "stay-with-me", "isbn": "978-0735218178",
         "price": 4000, "discount_price": 3200,
         "description": "A deeply moving exploration of marriage, family, and secrets in Nigeria.",
         "cover_image_url": "https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=400&fit=crop",
         "publisher": "Alfred A. Knopf", "pages": 272, "stock_quantity": 22,
         "is_featured": True, "is_bestseller": False,
         "category_slug": "african-literature", "author_names": ["Ayọ̀bámi Adébáyọ̀"]},

        {"title": "The Joys of Motherhood", "slug": "the-joys-of-motherhood", "isbn": "978-0807609507",
         "price": 2800,
         "description": "A classic exploration of womanhood, motherhood, and colonialism in Nigeria.",
         "cover_image_url": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&fit=crop",
         "publisher": "George Braziller", "pages": 224, "stock_quantity": 15,
         "is_featured": False, "is_bestseller": False,
         "category_slug": "african-literature", "author_names": ["Buchi Emecheta"]},

        # Science Fiction
        {"title": "Dune", "slug": "dune", "isbn": "978-0441013593",
         "price": 5200, "discount_price": 4500,
         "description": "Set on the desert planet Arrakis, this epic saga of politics, religion, and ecology is the world's bestselling science fiction novel.",
         "cover_image_url": "https://images.unsplash.com/photo-1518378188025-22bd89516ee2?w=400&fit=crop",
         "publisher": "Ace Books", "pages": 688, "stock_quantity": 35,
         "is_featured": True, "is_bestseller": True,
         "category_slug": "science-fiction", "author_names": ["Frank Herbert"]},

        {"title": "Foundation", "slug": "foundation", "isbn": "978-0553293357",
         "price": 4800,
         "description": "A visionary mathematician foresees the fall of the Galactic Empire and creates a plan to preserve knowledge.",
         "cover_image_url": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=400&fit=crop",
         "publisher": "Bantam Books", "pages": 296, "stock_quantity": 28,
         "is_featured": False, "is_bestseller": True,
         "category_slug": "science-fiction", "author_names": ["Isaac Asimov"]},

        {"title": "Binti", "slug": "binti", "isbn": "978-0765385253",
         "price": 2500,
         "description": "A young Himba woman must negotiate between her heritage and her dreams at the finest interplanetary university.",
         "cover_image_url": "https://images.unsplash.com/photo-1614729939124-032f0b56c9ce?w=400&fit=crop",
         "publisher": "Tor.com", "pages": 96, "stock_quantity": 40,
         "is_featured": True, "is_bestseller": False,
         "category_slug": "science-fiction", "author_names": ["Nnedi Okofor"]},

        # Business & Tech
        {"title": "Zero to One", "slug": "zero-to-one", "isbn": "978-0804139298",
         "price": 4200, "discount_price": 3500,
         "description": "Notes on startups, or how to build the future. Every moment in business happens only once.",
         "cover_image_url": "https://images.unsplash.com/photo-1553729459-efe14ef6055d?w=400&fit=crop",
         "publisher": "Crown Business", "pages": 224, "stock_quantity": 50,
         "is_featured": True, "is_bestseller": True,
         "category_slug": "business-tech", "author_names": ["Peter Thiel"]},

        {"title": "Clean Code", "slug": "clean-code", "isbn": "978-0132350884",
         "price": 5500,
         "description": "A handbook of agile software craftsmanship. Write code that is clean, readable, and maintainable.",
         "cover_image_url": "https://images.unsplash.com/photo-1515879218367-8466d910aeb9?w=400&fit=crop",
         "publisher": "Prentice Hall", "pages": 464, "stock_quantity": 20,
         "is_featured": False, "is_bestseller": False,
         "category_slug": "business-tech", "author_names": ["Robert C. Martin"]},

        {"title": "Outliers", "slug": "outliers", "isbn": "978-0316017930",
         "price": 3800, "discount_price": 3000,
         "description": "The story of success — what makes high-achievers different. Opportunity, culture, and legacy.",
         "cover_image_url": "https://images.unsplash.com/photo-1589998059171-988d887df646?w=400&fit=crop",
         "publisher": "Little Brown", "pages": 309, "stock_quantity": 32,
         "is_featured": False, "is_bestseller": True,
         "category_slug": "business-tech", "author_names": ["Malcolm Gladwell"]},

        # Self-Help
        {"title": "Atomic Habits", "slug": "atomic-habits", "isbn": "978-0735211292",
         "price": 4000, "discount_price": 3200,
         "description": "An easy & proven way to build good habits and break bad ones. Tiny changes, remarkable results.",
         "cover_image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400&fit=crop",
         "publisher": "Avery", "pages": 320, "stock_quantity": 60,
         "is_featured": True, "is_bestseller": True,
         "category_slug": "self-help", "author_names": ["James Clear"]},

        {"title": "The Subtle Art of Not Giving a F*ck", "slug": "subtle-art-not-giving", "isbn": "978-0062457714",
         "price": 3500,
         "description": "A counterintuitive approach to living a good life.",
         "cover_image_url": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=400&fit=crop",
         "publisher": "Harper", "pages": 224, "stock_quantity": 38,
         "is_featured": False, "is_bestseller": True,
         "category_slug": "self-help", "author_names": ["Mark Manson"]},
    ]

    for book in books_data:
        author_names = book.pop("author_names")
        category_slug = book.pop("category_slug")
        book["category_id"] = cat_ids.get(category_slug)
        book["id"] = str(uuid.uuid4())

        book_results = insert_if_not_exists("books", [book])
        if book_results:
            actual_book_id = book_results[0]["id"]
            # Link authors
            for name in author_names:
                auth_id = author_ids.get(name)
                if auth_id:
                    # Check if link exists
                    check = httpx.get(
                        f"{SUPABASE_URL}/rest/v1/book_authors?book_id=eq.{actual_book_id}&author_id=eq.{auth_id}",
                        headers=HEADERS, timeout=15.0,
                    )
                    if check.status_code == 200 and not check.json():
                        httpx.post(
                            f"{SUPABASE_URL}/rest/v1/book_authors",
                            headers={**HEADERS, "Prefer": "return=representation"},
                            json={"book_id": actual_book_id, "author_id": auth_id},
                            timeout=15.0,
                        )

    print(f"   [OK] {len(books_data)} books seeded with author links.")

    # --- Verify ---
    print("\n5. Verifying data...")
    for table in ["categories", "authors", "books", "book_authors"]:
        resp = httpx.get(
            f"{SUPABASE_URL}/rest/v1/{table}?select=count",
            headers={**HEADERS, "Prefer": "count=exact"},
            timeout=15.0,
        )
        count = resp.headers.get("content-range", "unknown")
        print(f"   {table}: {count}")

    print("\n" + "=" * 60)
    print("  [OK] Database setup complete!")
    print("=" * 60)


if __name__ == "__main__":
    run()
