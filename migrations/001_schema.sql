-- ==============================================================================
-- Schema: Buscador Centralizado de Librerías y Editoriales de Bolivia
-- Optimizado para PostgreSQL (Supabase / Neon / Self-Hosted)
-- ==============================================================================

-- 1. Extensiones necesarias para búsqueda fuzzy y normalización de tildes
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- 2. Tabla de Tiendas y Librerías
CREATE TABLE IF NOT EXISTS stores (
    store_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    city TEXT,
    website_url TEXT NOT NULL,
    logo_url TEXT,
    has_delivery BOOLEAN NOT NULL DEFAULT true,
    cms_type TEXT NOT NULL CHECK (cms_type IN ('woocommerce', 'shopify', 'wix', 'custom')),
    is_publisher_store BOOLEAN NOT NULL DEFAULT false,
    default_publisher_name TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Tabla de Editoriales (Publishers)
CREATE TABLE IF NOT EXISTS publishers (
    publisher_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    country TEXT DEFAULT 'Bolivia',
    website_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice GIN para búsqueda difusa en nombres de editoriales
CREATE INDEX IF NOT EXISTS idx_publishers_name_trgm 
    ON publishers USING gin (lower(unaccent(name)) gin_trgm_ops);

-- 4. Tabla Canónica de Libros
CREATE TABLE IF NOT EXISTS books (
    book_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    isbn TEXT,
    publisher_id BIGINT REFERENCES publishers(publisher_id) ON DELETE SET NULL,
    publisher_name TEXT NOT NULL DEFAULT 'No especificada',
    publisher_source TEXT NOT NULL DEFAULT 'unknown' 
        CHECK (publisher_source IN ('store_native', 'store_metadata', 'title_regex', 'api_enrichment', 'manual', 'unknown')),
    cover_image_url TEXT,
    synopsis TEXT,
    pages INTEGER,
    year_published INTEGER,
    needs_enrichment BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índices de búsqueda de alto rendimiento para libros
CREATE INDEX IF NOT EXISTS idx_books_isbn ON books (isbn) WHERE isbn IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_books_publisher_id ON books (publisher_id);
CREATE INDEX IF NOT EXISTS idx_books_title_trgm 
    ON books USING gin (lower(unaccent(title)) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_books_author_trgm 
    ON books USING gin (lower(unaccent(author)) gin_trgm_ops);

-- 5. Tabla de Ofertas de Libros por Tienda (Book Offers)
CREATE TABLE IF NOT EXISTS book_offers (
    offer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    book_id BIGINT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    store_id BIGINT NOT NULL REFERENCES stores(store_id) ON DELETE RESTRICT,
    price_bob NUMERIC(10, 2) NOT NULL CHECK (price_bob >= 0),
    is_in_stock BOOLEAN NOT NULL DEFAULT true,
    stock_label TEXT DEFAULT 'En stock',
    product_url TEXT NOT NULL,
    raw_sku TEXT,
    raw_title TEXT,
    last_checked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_book_store UNIQUE (book_id, store_id)
);

-- Índices en claves foráneas y filtros frecuentes
CREATE INDEX IF NOT EXISTS idx_offers_book_id ON book_offers (book_id);
CREATE INDEX IF NOT EXISTS idx_offers_store_id ON book_offers (store_id);

-- Índice parcial: acelera el listado de ofertas activas ordenadas por menor precio
CREATE INDEX IF NOT EXISTS idx_offers_active_price 
    ON book_offers (book_id, price_bob) 
    WHERE is_in_stock = true;
