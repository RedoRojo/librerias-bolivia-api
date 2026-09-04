import os
import sys

# Asegurar que la raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from app.core.database import SessionLocal
from app.models.store import Store
from app.models.book import Book
from app.models.offer import BookOffer
from app.normalizer.deduplicator import upsert_book_and_offer

def run_tests():
    db = SessionLocal()
    try:
        print("[TEST] Iniciando pruebas del normalizador y resolver de editoriales...")
        
        plural_store = db.query(Store).filter(Store.slug == "plural-editores").first()
        assert plural_store is not None, "Tienda Plural Editores no encontrada"

        lectura_store = db.query(Store).filter(Store.slug == "librerias-lectura").first()
        assert lectura_store is not None, "Tienda Librerías Lectura no encontrada"

        # Caso 1: Libro propio de editorial (Plural)
        item_plural = {
            "title": "Zambo Salvito",
            "author": "Antonio Paredes Candia",
            "price": "60.00",
            "product_url": "https://plural-editores.com/zambo-salvito",
            "is_in_stock": True
        }
        offer1 = upsert_book_and_offer(plural_store, item_plural, db, allow_network_api=False)
        book1 = offer1.book
        print(f"[TEST 1 OK] Libro: '{book1.title}', Editorial: '{book1.publisher_name}' (Origen: {book1.publisher_source})")
        assert book1.publisher_name == "Plural Editores"
        assert book1.publisher_source == "store_native"

        # Caso 2: Libro en tienda multimarca con editorial en título por regex
        item_lectura = {
            "title": "Ficciones (Alianza Editorial)",
            "author": "Jorge Luis Borges",
            "price": "95.00",
            "product_url": "https://libreriaslectura.com/ficciones-alianza",
            "is_in_stock": True
        }
        offer2 = upsert_book_and_offer(lectura_store, item_lectura, db, allow_network_api=False)
        book2 = offer2.book
        print(f"[TEST 2 OK] Libro: '{book2.title}', Editorial: '{book2.publisher_name}' (Origen: {book2.publisher_source})")
        assert book2.publisher_name == "Alianza Editorial"
        assert book2.publisher_source == "title_regex"

        # Caso 3: Deduplicación multi-tienda (el mismo libro ofrecido por otra tienda)
        item_plural_oferta = {
            "title": "Ficciones",
            "author": "Jorge Luis Borges",
            "price": "90.00",
            "product_url": "https://plural-editores.com/ficciones",
            "is_in_stock": True
        }
        offer3 = upsert_book_and_offer(plural_store, item_plural_oferta, db, allow_network_api=False)
        book3 = offer3.book
        
        # Debe haber emparejado con book2
        print(f"[TEST 3 OK] Comparador multi-tienda. Total ofertas para '{book3.title}': {len(book3.offers)}")
        assert book3.book_id == book2.book_id
        assert len(book3.offers) == 2
        
        precios = sorted([float(o.price_bob) for o in book3.offers])
        print(f"       Precios comparados ordenados: {precios} BOB")
        assert precios == [90.00, 95.00]

        print("\n🎉 ¡Todas las pruebas del normalizador y deduplicador pasaron con éxito!")
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
