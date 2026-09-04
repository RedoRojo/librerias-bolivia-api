import os
import sqlite3
import unicodedata
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import OperationalError
from app.core.config import settings

Base = declarative_base()

def remove_accents(s: str) -> str:
    """Elimina tildes y diacríticos para búsqueda insensible a acentos."""
    if not s:
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()

def similarity_score(s1: str, s2: str) -> float:
    """Calcula similitud de trigramas simple para emular pg_trgm en SQLite."""
    if not s1 or not s2:
        return 0.0
    s1, s2 = remove_accents(s1), remove_accents(s2)
    if s1 in s2 or s2 in s1:
        return 0.9
    def get_trigrams(text: str):
        text = f"  {text} "
        return set(text[i:i+3] for i in range(len(text) - 2))
    t1 = get_trigrams(s1)
    t2 = get_trigrams(s2)
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    return intersection / union if union > 0 else 0.0

def get_engine():
    """Inicializa el motor SQLAlchemy intentando PostgreSQL primero, con fallback a SQLite local si no hay servidor activo."""
    # 1. Intentar conectar a PostgreSQL
    try:
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

        engine = create_engine(
            db_url, 
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5} if "postgresql" in db_url else {}
        )
        with engine.connect() as conn:
            pass  # Prueba de conexión exitosa
        print(f"[DB] Conectado exitosamente a PostgreSQL: {db_url.split('@')[-1]}")
        return engine
    except Exception as e:
        if settings.USE_SQLITE_FALLBACK:
            os.makedirs(os.path.dirname(settings.SQLITE_LOCAL_PATH), exist_ok=True)
            sqlite_url = f"sqlite:///{settings.SQLITE_LOCAL_PATH}"
            print(f"[DB] Servidor PostgreSQL no disponible ({e}). Usando SQLite local para desarrollo: {sqlite_url}")
            engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
            
            # Registrar funciones personalizadas unaccent y similarity en SQLite para emular PostgreSQL
            @event.listens_for(engine, "connect")
            def set_sqlite_functions(dbapi_connection, connection_record):
                if isinstance(dbapi_connection, sqlite3.Connection):
                    dbapi_connection.create_function("unaccent", 1, remove_accents)
                    dbapi_connection.create_function("similarity", 2, similarity_score)
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
            return engine
        else:
            raise e

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
