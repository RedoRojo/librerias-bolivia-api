from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.book import Book
from app.models.store import Store
from app.models.offer import BookOffer
from app.normalizer.text_cleaner import clean_title, clean_author, clean_price, normalize_for_search
from app.normalizer.isbn import clean_isbn
from app.normalizer.editorial_resolver import resolve_editorial

def upsert_book_and_offer(
    store: Store,
    raw_item: Dict[str, Any],
    db: Session,
    allow_network_api: bool = True
) -> BookOffer:
    """
    Normaliza el libro, lo deduplica contra la base de datos y registra la oferta de la tienda.
    """
    initial_title = clean_title(raw_item.get("title"))
    if not initial_title:
        raise ValueError("El libro no tiene un título válido")
        
    author = clean_author(raw_item.get("author"))
    isbn = clean_isbn(raw_item.get("isbn"))
    price = clean_price(raw_item.get("price"))
    product_url = raw_item.get("product_url", "").strip()
    cover_image_url = raw_item.get("cover_image_url")
    synopsis = raw_item.get("synopsis")
    is_in_stock = bool(raw_item.get("is_in_stock", True))
    stock_label = raw_item.get("stock_label", "En stock" if is_in_stock else "Agotado")
    raw_sku = raw_item.get("raw_sku")

    # Resolver editorial y obtener título canónico sin sufijo de editorial
    pub_name, pub_source, pub_id, needs_enrich, canonical_title = resolve_editorial(
        store=store,
        raw_data={"title": initial_title, "author": author, "isbn": isbn, **raw_item},
        db=db,
        allow_network_api=allow_network_api
    )

    # 1. Búsqueda de coincidencia (Deduplicación)
    matched_book: Optional[Book] = None

    # Paso A: Coincidencia por ISBN
    if isbn:
        matched_book = db.query(Book).filter(Book.isbn == isbn).first()

    # Paso B: Coincidencia exacta por título canónico y autor
    if not matched_book and len(canonical_title) >= 3:
        query = db.query(Book).filter(func.lower(Book.title) == canonical_title.lower())
        if author:
            matched_book = query.filter(func.lower(Book.author) == author.lower()).first()
        else:
            matched_book = query.first()

    # Paso C: Coincidencia difusa de título
    if not matched_book and len(canonical_title) >= 4:
        norm_title = normalize_for_search(canonical_title)
        candidates = db.query(Book).limit(500).all()
        for cand in candidates:
            cand_norm = normalize_for_search(cand.title)
            # Si coinciden exactamente normalizados o uno contiene al otro
            if norm_title == cand_norm or (len(norm_title) >= 6 and (norm_title in cand_norm or cand_norm in norm_title)):
                if not author or not cand.author or author.lower() in cand.author.lower() or cand.author.lower() in author.lower():
                    matched_book = cand
                    break

    # 2. Si no existe, crear el libro canónico
    if not matched_book:
        matched_book = Book(
            title=canonical_title,
            author=author,
            isbn=isbn,
            publisher_id=pub_id,
            publisher_name=pub_name,
            publisher_source=pub_source,
            cover_image_url=cover_image_url,
            synopsis=synopsis,
            needs_enrichment=needs_enrich
        )
        db.add(matched_book)
        db.flush()
    else:
        # Enriquecer libro existente si tenemos mejores datos
        if not matched_book.cover_image_url and cover_image_url:
            matched_book.cover_image_url = cover_image_url
        if not matched_book.isbn and isbn:
            matched_book.isbn = isbn
        if not matched_book.synopsis and synopsis:
            matched_book.synopsis = synopsis
        if matched_book.publisher_name == "No especificada" and pub_name != "No especificada":
            matched_book.publisher_name = pub_name
            matched_book.publisher_id = pub_id
            matched_book.publisher_source = pub_source
            matched_book.needs_enrichment = needs_enrich

    # 3. Registrar o actualizar la oferta de la tienda (BookOffer)
    offer = db.query(BookOffer).filter(
        BookOffer.book_id == matched_book.book_id,
        BookOffer.store_id == store.store_id
    ).first()

    if not offer:
        offer = BookOffer(
            book_id=matched_book.book_id,
            store_id=store.store_id,
            price_bob=price,
            is_in_stock=is_in_stock,
            stock_label=stock_label,
            product_url=product_url,
            raw_sku=raw_sku,
            raw_title=raw_item.get("title")
        )
        db.add(offer)
    else:
        offer.price_bob = price
        offer.is_in_stock = is_in_stock
        offer.stock_label = stock_label
        offer.product_url = product_url
        offer.raw_sku = raw_sku
        offer.raw_title = raw_item.get("title")

    db.commit()
    db.refresh(offer)
    return offer
