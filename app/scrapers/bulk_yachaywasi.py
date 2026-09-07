import os
import sys
import re
import html
import time
import argparse
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Asegurar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal
from app.models.store import Store
from app.models.book import Book
from app.models.offer import BookOffer
from app.normalizer.text_cleaner import clean_title, clean_price
from app.normalizer.isbn import clean_isbn

ISBN_REGEX = re.compile(r'(97[89]\d{10})')
REBAJA_REGEX = re.compile(r'\s*\.?\s*REBAJA\s*\d+\s*BS\.?', re.IGNORECASE)

def parse_product(p: Dict[str, Any], store_id: int) -> Optional[Dict[str, Any]]:
    raw_title = html.unescape(p.get("title", "")).strip()
    if not raw_title:
        return None

    variants = p.get("variants", [])
    first_variant = variants[0] if variants else {}
    
    price = clean_price(first_variant.get("price", "0.00"))
    if not price or price <= 0:
        return None

    is_in_stock = bool(first_variant.get("available", True))
    stock_label = "En stock" if is_in_stock else "Agotado"
    raw_sku = first_variant.get("sku") or first_variant.get("barcode")

    # Extraer imágenes
    images = p.get("images", [])
    cover_image_url = images[0].get("src") if images else None

    raw_body = p.get("body_html") or ""
    synopsis = ""
    if raw_body:
        soup = BeautifulSoup(raw_body, "html.parser")
        synopsis = soup.get_text(separator=" ", strip=True)[:1500]

    # Extraer ISBN del SKU o URL de imagen o body
    isbn = clean_isbn(raw_sku) if raw_sku else None
    if not isbn:
        for img in images:
            m = ISBN_REGEX.search(img.get("src", ""))
            if m:
                isbn = m.group(1)
                break
    if not isbn and raw_body:
        m = ISBN_REGEX.search(raw_body)
        if m:
            isbn = m.group(1)

    # Extraer editorial (vendor)
    vendor = p.get("vendor", "").strip()
    publisher = vendor if vendor and vendor.lower() not in ("libreria yachaywasi", "yachaywasi", "generico", "default") else "No especificada"

    # Título y autor
    title = raw_title
    author = None

    if "|" in raw_title:
        parts = raw_title.split("|", 1)
        title = parts[0].strip()
        auth_part = parts[1].strip()
        if auth_part and auth_part.lower() not in ("varios", "varios autores", "diversos", "n/a"):
            author = auth_part.title()

    title = REBAJA_REGEX.sub('', title).strip()
    title = clean_title(title)
    if not title:
        return None

    if raw_body and not author:
        m_auth = re.search(r'AUTOR:\s*([^-\n<]+)', raw_body, re.IGNORECASE)
        if m_auth:
            auth_text = m_auth.group(1).strip()
            if auth_text.lower() not in ("varios", "varios autores"):
                author = auth_text.title()

    handle = p.get("handle")
    product_url = f"https://libreriayachaywasi.com/products/{handle}" if handle else "https://libreriayachaywasi.com/"

    return {
        "title": title,
        "author": author,
        "publisher_name": publisher,
        "publisher_source": "store_metadata",
        "price": price,
        "is_in_stock": is_in_stock,
        "stock_label": stock_label,
        "product_url": product_url,
        "cover_image_url": cover_image_url,
        "synopsis": synopsis,
        "isbn": isbn,
        "raw_sku": str(raw_sku) if raw_sku else None,
        "raw_title": raw_title
    }

def run_bulk_ingestion(start_page: int = 1, max_pages: Optional[int] = None, batch_limit: int = 250):
    db: Session = SessionLocal()
    store = db.query(Store).filter(Store.slug == "libreria-yachaywasi").first()
    if not store:
        print("❌ Tienda libreria-yachaywasi no encontrada.", flush=True)
        db.close()
        return

    print("==================================================================", flush=True)
    print(f"🚀 INICIANDO INGESTIÓN ULTRA-RÁPIDA PARA: {store.name}", flush=True)
    print(f"   URL: {store.website_url}", flush=True)
    print(f"   Página inicial: {start_page} | Máx páginas: {max_pages or 'Todas (~60 páginas)'}", flush=True)
    print("==================================================================", flush=True)

    # 1. Pre-cargar índices en memoria para cero latencia
    print("⚡ Cargando índice de libros existentes en memoria...", flush=True)
    existing_by_isbn: Dict[str, int] = {}
    existing_by_title: Dict[str, int] = {}
    for b_id, b_isbn, b_title in db.query(Book.book_id, Book.isbn, Book.title).all():
        if b_isbn:
            existing_by_isbn[b_isbn] = b_id
        if b_title:
            existing_by_title[b_title.lower()] = b_id
    print(f"   ✓ {len(existing_by_title)} libros ya indexados en memoria.", flush=True)

    client = httpx.Client(timeout=30.0, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    page = start_page
    total_processed = 0
    total_new_books = 0
    total_offers = 0
    start_time = time.time()

    try:
        while True:
            url = f"https://libreriayachaywasi.com/products.json?limit={batch_limit}&page={page}"
            try:
                page_start = time.time()
                resp = client.get(url)
                if resp.status_code != 200:
                    print(f"⚠️ Código HTTP {resp.status_code} en página {page}. Finalizando...", flush=True)
                    break
                
                data = resp.json()
                products = data.get("products", [])
                if not products:
                    print(f"🏁 No hay más productos en la página {page}. Catálogo completo finalizado.", flush=True)
                    break

                page_parsed: List[Dict[str, Any]] = []
                for p in products:
                    parsed = parse_product(p, store.store_id)
                    if parsed:
                        page_parsed.append(parsed)

                if not page_parsed:
                    page += 1
                    continue

                # 2. Separar libros nuevos vs existentes
                new_books_to_insert: List[Dict[str, Any]] = []
                seen_in_page_isbn = set()
                seen_in_page_title = set()

                for it in page_parsed:
                    isbn = it["isbn"]
                    t_lower = it["title"].lower()

                    matched_id = None
                    if isbn and isbn in existing_by_isbn:
                        matched_id = existing_by_isbn[isbn]
                    elif t_lower in existing_by_title:
                        matched_id = existing_by_title[t_lower]

                    if not matched_id:
                        # Evitar duplicados dentro de la misma página
                        if (isbn and isbn in seen_in_page_isbn) or (t_lower in seen_in_page_title):
                            continue
                        if isbn: seen_in_page_isbn.add(isbn)
                        seen_in_page_title.add(t_lower)

                        new_books_to_insert.append({
                            "title": it["title"],
                            "author": it["author"],
                            "isbn": it["isbn"],
                            "publisher_name": it["publisher_name"],
                            "publisher_source": it["publisher_source"],
                            "cover_image_url": it["cover_image_url"],
                            "synopsis": it["synopsis"]
                        })

                # 3. Inserción vectorial en lote de nuevos libros
                if new_books_to_insert:
                    stmt = pg_insert(Book).values(new_books_to_insert).returning(Book.book_id, Book.isbn, Book.title)
                    result = db.execute(stmt)
                    for row in result.fetchall():
                        r_id, r_isbn, r_title = row[0], row[1], row[2]
                        if r_isbn:
                            existing_by_isbn[r_isbn] = r_id
                        if r_title:
                            existing_by_title[r_title.lower()] = r_id
                    total_new_books += len(new_books_to_insert)

                # 4. Inserción vectorial de ofertas (BookOffer)
                offers_dict: Dict[int, Dict[str, Any]] = {}
                for it in page_parsed:
                    b_id = existing_by_isbn.get(it["isbn"]) if it["isbn"] else None
                    if not b_id:
                        b_id = existing_by_title.get(it["title"].lower())
                    if not b_id:
                        continue

                    # Un solo offer por book_id para evitar conflicto en el mismo lote
                    offers_dict[b_id] = {
                        "book_id": b_id,
                        "store_id": store.store_id,
                        "price_bob": it["price"],
                        "is_in_stock": it["is_in_stock"],
                        "stock_label": it["stock_label"],
                        "product_url": it["product_url"],
                        "raw_sku": it["raw_sku"],
                        "raw_title": it["raw_title"]
                    }

                if offers_dict:
                    offer_stmt = pg_insert(BookOffer).values(list(offers_dict.values()))
                    offer_stmt = offer_stmt.on_conflict_do_update(
                        constraint="uq_book_store",
                        set_={
                            "price_bob": offer_stmt.excluded.price_bob,
                            "is_in_stock": offer_stmt.excluded.is_in_stock,
                            "stock_label": offer_stmt.excluded.stock_label,
                            "product_url": offer_stmt.excluded.product_url,
                            "last_checked_at": func.now()
                        }
                    )
                    db.execute(offer_stmt)
                    total_offers += len(offers_dict)

                # Un solo commit por página
                db.commit()

                total_processed += len(page_parsed)
                page_duration = time.time() - page_start
                elapsed = time.time() - start_time
                avg_rate = total_processed / elapsed if elapsed > 0 else 0

                print(f"  [Pág {page:02d}] +{len(page_parsed):3d} libros ({len(new_books_to_insert):3d} nuevos) en {page_duration:.2f}s | Total: {total_processed:5d} libros | Promedio: {avg_rate:.0f} libros/s", flush=True)

                page += 1
                if max_pages and (page - start_page) >= max_pages:
                    print(f"🛑 Se alcanzó el límite configurado de {max_pages} páginas.", flush=True)
                    break

                time.sleep(0.1)

            except Exception as e:
                print(f"❌ Error en página {page}: {e}", flush=True)
                db.rollback()
                break

    finally:
        client.close()
        db.close()

    total_time = time.time() - start_time
    print("\n==================================================================", flush=True)
    print(f"🎉 CARGA MASIVA DE YACHAYWASI COMPLETADA", flush=True)
    print(f"   • Total libros procesados: {total_processed}", flush=True)
    print(f"   • Nuevos títulos indexados: {total_new_books}", flush=True)
    print(f"   • Ofertas de Yachaywasi activas: {total_offers}", flush=True)
    print(f"   • Tiempo total: {total_time:.1f} segundos ({total_processed / total_time if total_time > 0 else 0:.0f} libros/s)", flush=True)
    print("==================================================================", flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk Ingestion Vectorial para Librería Yachaywasi")
    parser.add_argument("--start-page", type=int, default=1, help="Página inicial")
    parser.add_argument("--pages", type=int, default=None, help="Número de páginas a procesar (None para todas)")
    args = parser.parse_args()

    run_bulk_ingestion(start_page=args.start_page, max_pages=args.pages)
