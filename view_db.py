import sqlite3
import sys

def show_tables():
    conn = sqlite3.connect("data/local_books.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    print("\n==================================================")
    print("📊 TABLAS EN LA BASE DE DATOS LOCAL (SQLite)")
    print("==================================================")
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [r[0] for r in c.fetchall()]

    for t in tables:
        c.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = c.fetchone()[0]
        print(f" • {t:<15} ({cnt} filas)")

    print("\n--------------------------------------------------")
    print("📚 ÚLTIMOS LIBROS GUARDADOS:")
    print("--------------------------------------------------")
    c.execute("""
        SELECT b.book_id, b.title, b.publisher_name, b.publisher_source, COUNT(o.offer_id) as ofertas
        FROM books b
        LEFT JOIN book_offers o ON b.book_id = o.book_id
        GROUP BY b.book_id
        ORDER BY b.book_id DESC
        LIMIT 10;
    """)
    rows = c.fetchall()
    for r in rows:
        print(f"[{r['book_id']:02d}] {r['title'][:32]:<32} | Editorial: {r['publisher_name'][:20]:<20} ({r['publisher_source']}) | Ofertas: {r['ofertas']}")

    print("\n--------------------------------------------------")
    print("🏪 LIBRERÍAS CONECTADAS Y OFERTAS:")
    print("--------------------------------------------------")
    c.execute("""
        SELECT s.name, s.cms_type, COUNT(o.offer_id) as total_ofertas
        FROM stores s
        LEFT JOIN book_offers o ON s.store_id = o.store_id
        GROUP BY s.store_id
        ORDER BY total_ofertas DESC;
    """)
    for r in c.fetchall():
        print(f" • {r['name']:<30} [{r['cms_type'].upper():<11}] -> {r['total_ofertas']} libros en stock")
    print("==================================================\n")
    conn.close()

if __name__ == "__main__":
    show_tables()
