import re
from sqlalchemy.orm import Session
from app.core.database import engine, Base, SessionLocal
from app.models.store import Store
from app.models.publisher import Publisher
from app.models.book import Book
from app.models.offer import BookOffer

INITIAL_STORES = [
    {
        "name": "Librerías Lectura",
        "slug": "librerias-lectura",
        "city": "La Paz / Santa Cruz",
        "website_url": "https://libreriaslectura.com/",
        "cms_type": "woocommerce",
        "is_publisher_store": False,
        "default_publisher_name": None
    },
    {
        "name": "SBS Librería Internacional",
        "slug": "sbs-libreria",
        "city": "La Paz / Cochabamba / Santa Cruz",
        "website_url": "https://www.sbs.com.bo/",
        "cms_type": "wix",
        "is_publisher_store": False,
        "default_publisher_name": None
    },
    {
        "name": "Librería Kronos",
        "slug": "libreria-kronos",
        "city": "La Paz",
        "website_url": "https://libreriakronos.com/",
        "cms_type": "shopify",
        "is_publisher_store": False,
        "default_publisher_name": None
    },
    {
        "name": "El Baúl del Libro",
        "slug": "el-baul-del-libro",
        "city": "Envíos Nacionales",
        "website_url": "https://bauldellibro.com/",
        "cms_type": "woocommerce",
        "is_publisher_store": False,
        "default_publisher_name": None
    },
    {
        "name": "Grupo Editorial Kipus",
        "slug": "editorial-kipus",
        "city": "Cochabamba",
        "website_url": "https://editorialkipus.com/",
        "cms_type": "woocommerce",
        "is_publisher_store": True,
        "default_publisher_name": "Editorial Kipus"
    },
    {
        "name": "Editorial El Cuervo",
        "slug": "editorial-el-cuervo",
        "city": "La Paz",
        "website_url": "https://www.editorialelcuervo.com/",
        "cms_type": "woocommerce",
        "is_publisher_store": True,
        "default_publisher_name": "Editorial El Cuervo"
    },
    {
        "name": "Plural Editores",
        "slug": "plural-editores",
        "city": "La Paz",
        "website_url": "https://plural-editores.com/",
        "cms_type": "woocommerce",
        "is_publisher_store": True,
        "default_publisher_name": "Plural Editores"
    },
    {
        "name": "Grupo Editorial La Hoguera",
        "slug": "la-hoguera",
        "city": "Santa Cruz",
        "website_url": "https://www.lahoguera.com/",
        "cms_type": "custom",
        "is_publisher_store": True,
        "default_publisher_name": "Editorial La Hoguera"
    },
    {
        "name": "Encantalibros",
        "slug": "encantalibros",
        "city": "La Paz / Envíos Nacionales",
        "website_url": "https://encantalibros.com/",
        "cms_type": "woocommerce",
        "is_publisher_store": False,
        "default_publisher_name": None
    },
    {
        "name": "Libroclik",
        "slug": "libroclik",
        "city": "Envíos Nacionales",
        "website_url": "https://libroclik.com/",
        "cms_type": "custom",
        "is_publisher_store": False,
        "default_publisher_name": None
    },
    {
        "name": "Vínculos",
        "slug": "vinculos",
        "city": "La Paz",
        "website_url": "https://vinculos.com.bo/",
        "cms_type": "woocommerce",
        "is_publisher_store": False,
        "default_publisher_name": None
    },
    {
        "name": "El Bagallero Ilustrado",
        "slug": "el-bagallero-ilustrado",
        "city": "Tarija / Envíos Nacionales",
        "website_url": "https://bagalleroilustrado.com/",
        "cms_type": "shopify",
        "is_publisher_store": False,
        "default_publisher_name": None
    },
    {
        "name": "Librería D&C",
        "slug": "libreria-dc",
        "city": "Envíos Nacionales",
        "website_url": "https://libreriadc.com.bo/",
        "cms_type": "woocommerce",
        "is_publisher_store": False,
        "default_publisher_name": None
    },
    {
        "name": "Librerías Don Bosco",
        "slug": "librerias-don-bosco",
        "city": "La Paz / Sucre",
        "website_url": "https://www.libreriasdonbosco.com/",
        "cms_type": "woocommerce",
        "is_publisher_store": False,
        "default_publisher_name": None
    }
]

INITIAL_PUBLISHERS = [
    {"name": "Plural Editores", "slug": "plural-editores", "country": "Bolivia"},
    {"name": "Editorial Kipus", "slug": "editorial-kipus", "country": "Bolivia"},
    {"name": "Editorial El Cuervo", "slug": "editorial-el-cuervo", "country": "Bolivia"},
    {"name": "Editorial La Hoguera", "slug": "editorial-la-hoguera", "country": "Bolivia"},
    {"name": "Editorial 3600", "slug": "editorial-3600", "country": "Bolivia"},
    {"name": "Nuevo Milenio", "slug": "nuevo-milenio", "country": "Bolivia"},
    {"name": "Gisbert", "slug": "gisbert", "country": "Bolivia"},
    {"name": "Alfaguara", "slug": "alfaguara", "country": "Internacional"},
    {"name": "Anagrama", "slug": "anagrama", "country": "Internacional"},
    {"name": "Alianza Editorial", "slug": "alianza-editorial", "country": "Internacional"},
    {"name": "Penguin Random House", "slug": "penguin-random-house", "country": "Internacional"},
    {"name": "Planeta", "slug": "planeta", "country": "Internacional"},
    {"name": "Cátedra", "slug": "catedra", "country": "Internacional"},
    {"name": "Debolsillo", "slug": "debolsillo", "country": "Internacional"},
    {"name": "Fondo de Cultura Económica", "slug": "fce", "country": "Internacional"}
]

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text)

def init_database():
    """Crea las tablas y siembra las 14 tiendas y editoriales base."""
    print("[DB] Creando tablas si no existen...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # Sembrar tiendas
        for s_data in INITIAL_STORES:
            existing = db.query(Store).filter(Store.slug == s_data["slug"]).first()
            if not existing:
                store = Store(**s_data)
                db.add(store)
            else:
                existing.website_url = s_data["website_url"]
                existing.cms_type = s_data["cms_type"]
                existing.is_publisher_store = s_data["is_publisher_store"]
                existing.default_publisher_name = s_data["default_publisher_name"]
        
        # Sembrar editoriales iniciales
        for p_data in INITIAL_PUBLISHERS:
            existing_p = db.query(Publisher).filter(Publisher.name == p_data["name"]).first()
            if not existing_p:
                pub = Publisher(**p_data)
                db.add(pub)
                
        db.commit()
        print(f"[DB] Inicialización completada exitosamente. Tiendas registradas: {len(INITIAL_STORES)}")
    except Exception as e:
        db.rollback()
        print(f"[DB] Error durante la siembra de base de datos: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
