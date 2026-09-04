# Librerías Bolivia API 🇧🇴📚

API REST y comparador de precios de libros en Bolivia que consolida información y disponibilidad en tiempo real de **14 librerías y editoriales** del país (La Paz, Santa Cruz, Cochabamba, Tarija, Sucre y envíos nacionales).

---

## 🚀 Tecnologías
- **Framework**: FastAPI (Python 3.12+)
- **Base de Datos**: PostgreSQL (con extensiones `pg_trgm` y `unaccent` para búsqueda difusa insensible a mayúsculas y tildes) con fallback automático a SQLite local.
- **ORM**: SQLAlchemy 2.0
- **Extracción Estructurada**: Adaptadores nativos para **Shopify** (`/products.json`), **WooCommerce** (Store API REST) y BeautifulSoup.
- **Deduplicador & Normalizador de Editoriales**:
  - Algoritmo en Cascada de 4 niveles para garantizar la editorial canónica de cada libro.
  - Agrupación automática de libros vendidos por múltiples librerías en una ficha única con comparador de ofertas ordenadas de menor a mayor precio.

---

## 📂 Estructura del Repositorio
```
librerias-bolivia-api/
├── app/
│   ├── api/              # Endpoints REST (books, stores, publishers)
│   ├── core/             # Configuración y conexión de base de datos
│   ├── models/           # Modelos SQLAlchemy (Store, Publisher, Book, BookOffer)
│   ├── normalizer/       # Algoritmos de deduplicación y resolución de editoriales
│   └── scrapers/         # Adaptadores Shopify, WooCommerce y Runner CLI
├── migrations/
│   ├── 001_schema.sql    # DDL PostgreSQL para producción (Supabase / Neon)
│   └── 002_seed_stores.sql # Semilla oficial de las 14 tiendas y editoriales
├── tests/                # Pruebas automatizadas (normalizer y API)
├── main.py               # Entrada principal de FastAPI
├── view_db.py            # Visor CLI rápido de base de datos
├── Dockerfile            # Contenedor optimizado para despliegue
├── render.yaml           # Configuración Render Blueprint
├── requirements.txt      # Dependencias Python
└── DEPLOY.md             # Guía paso a paso de despliegue gratuito
```

---

## ⚡ Guía Rápida de Uso

### 1. Iniciar el Servidor API
```bash
uvicorn main:app --reload --port 8000
```
Documentación Swagger disponible en: `http://localhost:8000/docs`

### 2. Extraer Libros desde la Terminal (Scrapers)
```bash
# Extraer de Librería Kronos (Shopify)
python app/scrapers/runner.py --store libreria-kronos --limit 20

# Extraer de Plural Editores (WooCommerce)
python app/scrapers/runner.py --store plural-editores --limit 20

# Extraer de Encantalibros (WooCommerce)
python app/scrapers/runner.py --store encantalibros --limit 20

# Extraer de El Bagallero Ilustrado (Shopify)
python app/scrapers/runner.py --store el-bagallero-ilustrado --limit 20

# Extraer de todas las librerías
python app/scrapers/runner.py --all --limit 50
```

### 3. Ejecutar Pruebas Automatizadas
```bash
python tests/test_normalizer.py
python tests/test_api.py
```

### 4. Ver los Datos Guardados por Consola
```bash
python view_db.py
```
