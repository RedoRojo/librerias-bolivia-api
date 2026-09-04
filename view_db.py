import os
import sys

# Asegurar que la raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import SessionLocal, settings
from app.models.store import Store
from app.models.publisher import Publisher
from app.models.book import Book
from app.models.offer import BookOffer

def show_tables():
    db = SessionLocal()
    db_target = "PostgreSQL (Supabase)" if "postgresql" in settings.DATABASE_URL else "SQLite Local"
    try:
        print("\n==================================================")
        print(f"📊 TABLAS EN LA BASE DE DATOS: {db_target}")
        print("==================================================")
        
        stores_cnt = db.query(Store).count()
        publishers_cnt = db.query(Publisher).count()
        books_cnt = db.query(Book).count()
        offers_cnt = db.query(BookOffer).count()

        print(f" • {'stores':<15} ({stores_cnt} filas)")
        print(f" • {'publishers':<15} ({publishers_cnt} filas)")
        print(f" • {'books':<15} ({books_cnt} filas)")
        print(f" • {'book_offers':<15} ({offers_cnt} filas)")

        if books_cnt > 0:
            print("\n--------------------------------------------------")
            print("📚 ÚLTIMOS LIBROS GUARDADOS:")
            print("--------------------------------------------------")
            books = db.query(Book).order_by(Book.book_id.desc()).limit(10).all()
            for b in books:
                print(f"[{b.book_id:02d}] {b.title[:32]:<32} | Editorial: {b.publisher_name[:20]:<20} ({b.publisher_source}) | Ofertas: {len(b.offers)}")

        print("\n--------------------------------------------------")
        print("🏪 LIBRERÍAS CONECTADAS Y OFERTAS:")
        print("--------------------------------------------------")
        stores = db.query(Store).all()
        for s in stores:
            o_cnt = len(s.offers)
            print(f" • {s.name:<30} [{s.cms_type.upper():<11}] -> {o_cnt} libros en stock")
        print("==================================================\n")
    finally:
        db.close()

if __name__ == "__main__":
    show_tables()
