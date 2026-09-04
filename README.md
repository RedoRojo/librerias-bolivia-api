# Buscador Centralizado de Librerías y Editoriales de Bolivia 🇧🇴📚

Plataforma unificada y comparador de precios de libros en Bolivia que consolida información de **14 librerías y editoriales** oficiales (La Paz, Santa Cruz, Cochabamba, Tarija, Sucre y envíos nacionales).

---

## 🚀 Arquitectura y Tecnologías
- **Backend**: FastAPI (Python 3.12+)
- **Base de Datos**: PostgreSQL (con extensiones `pg_trgm` y `unaccent` para búsqueda fuzzy sin tildes) y fallback local SQLite.
- **ORM / Migraciones**: SQLAlchemy 2.0 + scripts DDL en `backend/migrations/`
- **Extracción**: Adaptadores estructurados para **Shopify** (`/products.json`), **WooCommerce** (Store API REST) y BeautifulSoup.
- **Normalización Inteligente**:
  - Limpieza de ISBN (10 y 13 dígitos)
  - Limpieza de precios en Bolivianos (`NUMERIC(10, 2)`)
  - **Algoritmo en Cascada de 4 Niveles** para resolver la **Editorial**:
    1. *Nivel 1*: Editorial propia de la tienda (*Plural, Kipus, El Cuervo, La Hoguera*).
    2. *Nivel 2*: Metadatos/atributos de la tienda (`editorial`, `sello`, `brand`).
    3. *Nivel 3*: Detección por regex en títulos (ej. `"Rayuela (Alfaguara)"`).
    4. *Nivel 4*: Enriquecimiento automático vía APIs públicas gratuitas (Google Books / OpenLibrary).
  - **Deduplicación**: Agrupa el mismo libro vendido por diferentes tiendas en una ficha única con comparador de precios ordenado.

---

## 📂 Estructura del Proyecto
```
buscador_librerias_bolivia/
├── backend/
│   ├── app/
│   │   ├── api/              # Endpoints REST (books, stores, publishers)
│   │   ├── core/             # Configuración, DB engine e inicialización
│   │   ├── models/           # Modelos SQLAlchemy (Store, Publisher, Book, BookOffer)
│   │   ├── normalizer/       # Algoritmos de deduplicación y resolución de editorial
│   │   └── scrapers/         # Adaptadores Shopify, WooCommerce y Runner CLI
│   ├── migrations/
│   │   ├── 001_schema.sql    # DDL PostgreSQL con índices GIN y partial indexes
│   │   └── 002_seed_stores.sql # Semilla de las 14 tiendas y editoriales
│   ├── tests/                # Pruebas automatizadas de API y normalizador
│   └── main.py               # Entrada principal FastAPI
├── data/
│   └── local_books.db        # Base SQLite local para desarrollo
├── requirements.txt
└── .env.example
```

---

## ⚡ Guía Rápida de Uso

### 1. Iniciar el Servidor Backend
```bash
cd buscador_librerias_bolivia
PYTHONPATH=backend .venv/bin/uvicorn main:app --reload --port 8000
```
La documentación interactiva Swagger estará disponible en: `http://localhost:8000/docs`

### 2. Ejecutar Extracción de Libros (Scrapers)
Para poblar el catálogo de una librería específica:
```bash
# Extraer de Librería Kronos (Shopify)
PYTHONPATH=backend .venv/bin/python backend/app/scrapers/runner.py --store libreria-kronos --limit 20

# Extraer de Plural Editores (WooCommerce)
PYTHONPATH=backend .venv/bin/python backend/app/scrapers/runner.py --store plural-editores --limit 20

# Extraer de Encantalibros (WooCommerce)
PYTHONPATH=backend .venv/bin/python backend/app/scrapers/runner.py --store encantalibros --limit 20

# Extraer de todas las librerías
PYTHONPATH=backend .venv/bin/python backend/app/scrapers/runner.py --all --limit 50
```

### 3. Ejecutar las Pruebas Automatizadas
```bash
PYTHONPATH=backend .venv/bin/python backend/tests/test_normalizer.py
PYTHONPATH=backend .venv/bin/python backend/tests/test_api.py
```

### 4. Despliegue en Producción con PostgreSQL (Supabase / Neon / RDS)
1. Crea tu base de datos en Supabase, Neon o PostgreSQL VPS.
2. Ejecuta los scripts en `backend/migrations/001_schema.sql` y `002_seed_stores.sql`.
3. Configura la variable de entorno:
   `export DATABASE_URL="postgresql+psycopg://usuario:password@host:5432/nombre_bd"`
4. ¡El backend se conectará directamente a PostgreSQL en producción!
