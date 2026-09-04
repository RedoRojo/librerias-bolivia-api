from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.config import settings
from app.core.database import get_db
from app.core.init_db import init_database
from app.models.book import Book
from app.models.offer import BookOffer
from app.models.store import Store
from app.models.publisher import Publisher
from app.api.books import router as books_router
from app.api.stores import router as stores_router
from app.api.publishers import router as publishers_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para el buscador y comparador centralizado de librerías y editoriales de Bolivia.",
    version="1.0.0"
)

# CORS habilitado para conectar cualquier frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(books_router, prefix=settings.API_V1_STR)
app.include_router(stores_router, prefix=settings.API_V1_STR)
app.include_router(publishers_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def on_startup():
    print("[SERVER] Iniciando aplicación y verificando base de datos...")
    try:
        init_database()
    except Exception as e:
        print(f"[SERVER] Error en inicio de BD: {e}")

@app.get("/")
def root():
    return {
        "message": "Bienvenido al Buscador Centralizado de Librerías y Editoriales de Bolivia",
        "docs": "/docs",
        "endpoints": {
            "search": "/api/books/search?q=...",
            "stores": "/api/stores",
            "publishers": "/api/publishers",
            "stats": "/api/stats"
        }
    }

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_books = db.query(func.count(Book.book_id)).scalar() or 0
    total_offers = db.query(func.count(BookOffer.offer_id)).scalar() or 0
    total_stores = db.query(func.count(Store.store_id)).filter(Store.is_active == True).scalar() or 0
    total_publishers = db.query(func.count(Publisher.publisher_id)).scalar() or 0
    
    return {
        "total_books_indexed": total_books,
        "total_offers_active": total_offers,
        "total_stores_covered": total_stores,
        "total_publishers": total_publishers
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
