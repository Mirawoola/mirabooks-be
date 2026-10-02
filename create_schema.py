"""Create tables in Supabase via direct PostgreSQL connection."""
import psycopg2

# Use IPv6 address directly since DNS resolves to IPv6 only
# Or try the pooler endpoint which often has IPv4
DB_URLS = [
    "postgresql://postgres:Olamikusibe23.@db.aymbzilbsmwucmdhlfey.supabase.co:5432/postgres",
    "postgresql://postgres.aymbzilbsmwucmdhlfey:Olamikusibe23.@aws-0-eu-central-1.pooler.supabase.com:6543/postgres",
    "postgresql://postgres.aymbzilbsmwucmdhlfey:Olamikusibe23.@aws-0-eu-west-1.pooler.supabase.com:6543/postgres",
    "postgresql://postgres.aymbzilbsmwucmdhlfey:Olamikusibe23.@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
    "postgresql://postgres.aymbzilbsmwucmdhlfey:Olamikusibe23.@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres",
]

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    image_url TEXT,
    display_order INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS authors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    bio TEXT,
    image_url TEXT
);

CREATE TABLE IF NOT EXISTS books (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    isbn TEXT,
    price DECIMAL(10,2) NOT NULL,
    discount_price DECIMAL(10,2),
    description TEXT,
    cover_image_url TEXT,
    publisher TEXT,
    publication_date DATE,
    pages INT,
    language TEXT DEFAULT 'English',
    format TEXT DEFAULT 'Paperback',
    stock_quantity INT DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    is_bestseller BOOLEAN DEFAULT FALSE,
    category_id UUID REFERENCES categories(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS book_authors (
    book_id UUID REFERENCES books(id) ON DELETE CASCADE,
    author_id UUID REFERENCES authors(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, author_id)
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    phone TEXT,
    avatar_url TEXT,
    auth_provider TEXT DEFAULT 'google',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS addresses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    street TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    postal_code TEXT DEFAULT '',
    country TEXT DEFAULT 'Nigeria',
    is_default BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS carts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cart_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cart_id UUID REFERENCES carts(id) ON DELETE CASCADE,
    book_id UUID REFERENCES books(id),
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    order_number TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'pending',
    subtotal DECIMAL(10,2) NOT NULL,
    shipping_cost DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    shipping_method TEXT DEFAULT 'standard',
    payment_reference TEXT,
    payment_status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    book_id UUID REFERENCES books(id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS shipping_addresses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    street TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    postal_code TEXT DEFAULT '',
    country TEXT DEFAULT 'Nigeria'
);
"""

conn = None
for url in DB_URLS:
    try:
        print(f"Trying: {url[:60]}...")
        conn = psycopg2.connect(url, connect_timeout=10)
        print("Connected!")
        break
    except Exception as e:
        print(f"  Failed: {e}")

if conn:
    conn.autocommit = True
    cur = conn.cursor()
    print("Creating tables...")
    cur.execute(SCHEMA_SQL)
    print("Tables created!")
    cur.close()
    conn.close()
else:
    print("Could not connect to any PostgreSQL endpoint.")
    print("Please run the SQL schema manually in Supabase Dashboard SQL Editor.")
