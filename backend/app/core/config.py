import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Buscador de Librerías de Bolivia"
    API_V1_STR: str = "/api"
    
    # URL de conexión a la base de datos (PostgreSQL por defecto, ej: Supabase, Neon o Local)
    # Ejemplo: postgresql+psycopg://postgres:password@localhost:5432/libros_bolivia
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg://postgres:postgres@localhost:5432/libros_bolivia"
    )
    
    # Fallback local a SQLite para desarrollo sin servidor PostgreSQL activo
    USE_SQLITE_FALLBACK: bool = os.getenv("USE_SQLITE_FALLBACK", "true").lower() in ("true", "1", "yes")
    SQLITE_LOCAL_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../data/local_books.db")
    
    # Configuración de crawlers
    CRAWLER_USER_AGENT: str = "LibreriasBoliviaBot/1.0 (+https://librerias-bolivia.com/bot; contacto@librerias-bolivia.com)"
    REQUEST_TIMEOUT_SECONDS: int = 15
    RATE_LIMIT_DELAY: float = 1.0  # Pausa cortés entre peticiones a una misma tienda
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
