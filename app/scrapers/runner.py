import os
import sys

# Asegurar que la raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.store import Store
from app.models.book import Book
from app.normalizer.deduplicator import upsert_book_and_offer
from app.scrapers.shopify_adapter import ShopifyAdapter
from app.scrapers.woocommerce_adapter import WooCommerceAdapter
from app.scrapers.base import logger

def get_adapter_for_store(store: Store):
    """Retorna la instancia del adaptador adecuado según el CMS de la librería."""
    if store.cms_type == "shopify":
        return ShopifyAdapter(store_name=store.name, base_url=store.website_url)
    elif store.cms_type == "woocommerce":
        return WooCommerceAdapter(store_name=store.name, base_url=store.website_url)
    else:
        # Para tiendas custom o wix, se utiliza el extractor BeautifulSoup / HTTP estándar
        return WooCommerceAdapter(store_name=store.name, base_url=store.website_url)

def run_scraper_for_store(store: Store, db: Session, limit: Optional[int] = None):
    """Ejecuta la extracción de una tienda y guarda los libros en la base de datos."""
    print(f"\n==================================================================")
    print(f"🚀 Iniciando extracción para: {store.name} ({store.website_url})")
    print(f"   CMS: {store.cms_type.upper()} | Editorial Propia: {'Sí' if store.is_publisher_store else 'No'}")
    print(f"==================================================================")

    adapter = get_adapter_for_store(store)
    count = 0
    errors = 0

    try:
        with adapter:
            for raw_item in adapter.scrape(max_items=limit):
                try:
                    offer = upsert_book_and_offer(
                        store=store,
                        raw_item=raw_item,
                        db=db,
                        allow_network_api=True
                    )
                    count += 1
                    book = offer.book
                    print(f"[{count:03d}] 📖 '{book.title[:38]:<38}' | 🏢 {book.publisher_name[:22]:<22} | 💰 {offer.price_bob:>6.2f} Bs ({offer.stock_label})")
                except Exception as item_err:
                    errors += 1
                    logger.debug(f"Error procesando item: {item_err}")
    except Exception as e:
        logger.error(f"Error general en extractor de {store.name}: {e}")

    print(f"\n✅ Finalizado {store.name}: {count} libros procesados, {errors} errores.")
    return count

def main():
    parser = argparse.ArgumentParser(description="Ejecutor de crawlers de librerías bolivianas")
    parser.add_argument("--store", type=str, help="Slug de la tienda (ej: libreria-kronos, plural-editores)")
    parser.add_argument("--all", action="store_true", help="Ejecutar todas las tiendas registradas")
    parser.add_argument("--limit", type=int, default=20, help="Límite de libros a extraer por tienda (default: 20 para pruebas)")
    args = parser.parse_args()

    db: Session = SessionLocal()
    try:
        if args.store:
            store = db.query(Store).filter(Store.slug == args.store).first()
            if not store:
                print(f"❌ Tienda con slug '{args.store}' no encontrada.")
                sys.exit(1)
            run_scraper_for_store(store, db, limit=args.limit)
        elif args.all:
            stores = db.query(Store).filter(Store.is_active == True).all()
            total = 0
            for s in stores:
                total += run_scraper_for_store(s, db, limit=args.limit)
            print(f"\n🎉 Extracción completa terminada. Total libros/ofertas indexados: {total}")
        else:
            print("Especifique --store <slug> o --all. Lista de tiendas disponibles:")
            for s in db.query(Store).all():
                print(f"  • {s.slug:<25} ({s.name})")
    finally:
        db.close()

if __name__ == "__main__":
    main()
