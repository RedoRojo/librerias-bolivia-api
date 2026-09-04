from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_api_health_and_stats():
    print("[TEST] Verificando salud del servidor...")
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    print("  ✓ /api/health respondió 200 OK")

    print("[TEST] Verificando estadísticas del catálogo...")
    resp_stats = client.get("/api/stats")
    assert resp_stats.status_code == 200
    stats = resp_stats.json()
    print(f"  ✓ /api/stats: {stats['total_books_indexed']} libros, {stats['total_offers_active']} ofertas, {stats['total_stores_covered']} tiendas.")
    assert stats["total_stores_covered"] == 14

def test_search_and_comparator():
    print("[TEST] Verificando búsqueda de libros...")
    resp = client.get("/api/books/search")
    assert resp.status_code == 200
    data = resp.json()
    print(f"  ✓ /api/books/search: {data['total']} libros encontrados.")
    
    # Probar búsqueda por palabra clave
    resp_keyword = client.get("/api/books/search?q=dictador")
    assert resp_keyword.status_code == 200
    kw_data = resp_keyword.json()
    if kw_data["total"] > 0:
        book = kw_data["results"][0]
        print(f"  ✓ Búsqueda 'dictador': '{book['title']}' por {book['publisher_name']} (Ofertas: {book['offers_count']})")
        assert len(book["offers"]) >= 1

    # Probar endpoint de librerías
    resp_stores = client.get("/api/stores")
    assert resp_stores.status_code == 200
    stores = resp_stores.json()
    print(f"  ✓ /api/stores: {len(stores)} tiendas listadas.")
    assert len(stores) == 14

    print("\n🎉 ¡Todas las pruebas de la API FastAPI pasaron con éxito!")

if __name__ == "__main__":
    test_api_health_and_stats()
    test_search_and_comparator()
