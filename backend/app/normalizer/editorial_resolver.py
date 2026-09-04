import re
import urllib.request
import urllib.parse
import json
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.publisher import Publisher
from app.models.store import Store

# Lista de editoriales reconocidas para búsqueda heurística en títulos
KNOWN_PUBLISHERS = [
    "Alfaguara", "Anagrama", "Alianza Editorial", "Alianza", "Planeta", 
    "Penguin Random House", "Debolsillo", "Cátedra", "Tusquets", 
    "Fondo de Cultura Económica", "FCE", "Salamandra", "Siruela", 
    "Akal", "Norma", "Santillana", "SM", "Gredos", "Plural Editores", 
    "Plural", "Editorial Kipus", "Kipus", "Editorial El Cuervo", "El Cuervo", 
    "Editorial La Hoguera", "La Hoguera", "Editorial 3600", "3600", 
    "Nuevo Milenio", "Gisbert", "Sexto Piso", "Impedimenta", "Acantilado",
    "Paidós", "Siglo XXI", "Trotta", "Herder", "Editorial Verbo Divino"
]

def get_or_create_publisher(name: str, db: Session) -> Tuple[str, Optional[int]]:
    """Busca o crea una editorial en la base de datos y retorna su nombre limpio y publisher_id."""
    clean_name = name.strip()
    # Estandarizaciones comunes
    if clean_name.lower() in ("plural", "plural editores"):
        clean_name = "Plural Editores"
    elif clean_name.lower() in ("kipus", "editorial kipus"):
        clean_name = "Editorial Kipus"
    elif clean_name.lower() in ("el cuervo", "editorial el cuervo"):
        clean_name = "Editorial El Cuervo"
    elif clean_name.lower() in ("la hoguera", "editorial la hoguera"):
        clean_name = "Editorial La Hoguera"
    elif clean_name.lower() in ("alianza", "alianza editorial"):
        clean_name = "Alianza Editorial"

    # Buscar existente
    pub = db.query(Publisher).filter(Publisher.name.ilike(clean_name)).first()
    if pub:
        return pub.name, pub.publisher_id
        
    # Crear nueva editorial
    slug = re.sub(r'[^\w\s-]', '', clean_name.lower()).replace(' ', '-')
    try:
        new_pub = Publisher(name=clean_name, slug=slug, country="Bolivia" if "bolivia" in clean_name.lower() else "Desconocido")
        db.add(new_pub)
        db.flush()
        return new_pub.name, new_pub.publisher_id
    except Exception:
        db.rollback()
        pub = db.query(Publisher).filter(Publisher.name == clean_name).first()
        if pub:
            return pub.name, pub.publisher_id
        return clean_name, None

def resolve_editorial(
    store: Store, 
    raw_data: Dict[str, Any], 
    db: Session, 
    allow_network_api: bool = True
) -> Tuple[str, str, Optional[int], bool, str]:
    """
    Algoritmo en Cascada de 4 Niveles para resolver la Editorial:
    Retorna: (publisher_name, publisher_source, publisher_id, needs_enrichment, cleaned_title)
    """
    title = raw_data.get("title", "").strip()
    isbn = raw_data.get("isbn")
    author = raw_data.get("author")
    cleaned_title = title
    
    # -------------------------------------------------------------
    # Nivel 1: Tienda Editorial Propia (Garantía 100%)
    # -------------------------------------------------------------
    if store.is_publisher_store and store.default_publisher_name:
        pub_name, pub_id = get_or_create_publisher(store.default_publisher_name, db)
        return pub_name, "store_native", pub_id, False, cleaned_title

    # -------------------------------------------------------------
    # Nivel 2: Metadatos y Atributos de la Tienda
    # -------------------------------------------------------------
    raw_pub = raw_data.get("editorial") or raw_data.get("publisher") or raw_data.get("vendor") or raw_data.get("brand")
    if raw_pub and str(raw_pub).strip() and str(raw_pub).strip().lower() not in ("generico", "varios", "ninguna", "n/a", "null"):
        pub_name, pub_id = get_or_create_publisher(str(raw_pub), db)
        return pub_name, "store_metadata", pub_id, False, cleaned_title

    # -------------------------------------------------------------
    # Nivel 3: Heurística y Minería de Texto en Título y Sinopsis
    # -------------------------------------------------------------
    # Patrón 1: "(Editorial X)" o "(X)" al final del título
    match_paren = re.search(r'\s*\((?:Editorial\s+)?([A-Za-zÀ-ÿ0-9\s]{3,35})\)$', title)
    if match_paren:
        candidate = match_paren.group(1).strip()
        # Verificar que no sea un año como "(2022)" ni una edición "(2da ed)"
        if not candidate.isdigit() and not re.search(r'\b(ed|tomo|vol|volumen|edicion|ilustrado)\b', candidate, re.I):
            pub_name, pub_id = get_or_create_publisher(candidate, db)
            cleaned_title = title[:match_paren.start()].strip()
            return pub_name, "title_regex", pub_id, False, cleaned_title

    # Patrón 2: Coincidencia con editoriales conocidas en título
    for known in KNOWN_PUBLISHERS:
        pattern = rf'\s*(?:-\s*|\(\s*|\bpor\s+)(?:Editorial\s+)?({re.escape(known)})\b(?:\))?'
        m = re.search(pattern, title, re.IGNORECASE)
        if m:
            pub_name, pub_id = get_or_create_publisher(known, db)
            cleaned_title = title[:m.start()].strip()
            return pub_name, "title_regex", pub_id, False, cleaned_title

    # -------------------------------------------------------------
    # Nivel 4: Enriquecimiento Automático vía APIs Públicas Gratuitas
    # -------------------------------------------------------------
    if allow_network_api:
        # A. Intentar con Google Books API usando ISBN
        if isbn:
            try:
                url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
                req = urllib.request.Request(url, headers={"User-Agent": "LibreriasBolivia/1.0"})
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if data.get("totalItems", 0) > 0:
                            vol_info = data["items"][0].get("volumeInfo", {})
                            api_pub = vol_info.get("publisher")
                            if api_pub:
                                pub_name, pub_id = get_or_create_publisher(api_pub, db)
                                return pub_name, "api_enrichment", pub_id, False, cleaned_title
            except Exception:
                pass

        # B. Intentar con OpenLibrary API usando ISBN
        if isbn:
            try:
                url = f"https://openlibrary.org/isbn/{isbn}.json"
                req = urllib.request.Request(url, headers={"User-Agent": "LibreriasBolivia/1.0"})
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        pubs = data.get("publishers", [])
                        if pubs and pubs[0]:
                            pub_name, pub_id = get_or_create_publisher(pubs[0], db)
                            return pub_name, "api_enrichment", pub_id, False, cleaned_title
            except Exception:
                pass

        # C. Intentar con Google Books API usando Título + Autor si no hay ISBN
        if title and author and len(title) > 4:
            try:
                q = f"intitle:{urllib.parse.quote(title)}+inauthor:{urllib.parse.quote(author)}"
                url = f"https://www.googleapis.com/books/v1/volumes?q={q}&maxResults=1"
                req = urllib.request.Request(url, headers={"User-Agent": "LibreriasBolivia/1.0"})
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if data.get("totalItems", 0) > 0:
                            vol_info = data["items"][0].get("volumeInfo", {})
                            api_pub = vol_info.get("publisher")
                            if api_pub:
                                pub_name, pub_id = get_or_create_publisher(api_pub, db)
                                return pub_name, "api_enrichment", pub_id, False, cleaned_title
            except Exception:
                pass

    # -------------------------------------------------------------
    # Fallback Elegante
    # -------------------------------------------------------------
    return "No especificada", "unknown", None, True, cleaned_title
