from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, desc, asc
from app.core.database import get_db
from app.models.book import Book
from app.models.offer import BookOffer
from app.models.store import Store
from app.models.publisher import Publisher
from app.normalizer.text_cleaner import normalize_for_search
from pydantic import BaseModel

router = APIRouter(prefix="/books", tags=["Books"])

class OfferOut(BaseModel):
    offer_id: int
    store_id: int
    store_name: str
    store_slug: str
    store_city: Optional[str]
    price_bob: float
    is_in_stock: bool
    stock_label: str
    product_url: str

class BookSummaryOut(BaseModel):
    book_id: int
    title: str
    author: Optional[str]
    isbn: Optional[str]
    publisher_name: str
    cover_image_url: Optional[str]
    synopsis: Optional[str]
    best_price_bob: Optional[float]
    offers_count: int
    available_in_stock: bool
    offers: List[OfferOut]

class BookSearchResponse(BaseModel):
    total: int
    limit: int
    offset: int
    results: List[BookSummaryOut]

@router.get("/search", response_model=BookSearchResponse)
def search_books(
    q: Optional[str] = Query(None, description="Término de búsqueda: título, autor o ISBN"),
    publisher_id: Optional[int] = Query(None, description="Filtrar por ID de editorial"),
    store_id: Optional[int] = Query(None, description="Filtrar por ID de librería"),
    city: Optional[str] = Query(None, description="Filtrar por ciudad (ej: La Paz, Santa Cruz, Cochabamba)"),
    max_price: Optional[float] = Query(None, description="Precio máximo en Bolivianos"),
    in_stock_only: bool = Query(False, description="Solo libros con stock disponible"),
    sort: str = Query("relevance", description="Orden: relevance, price_asc, price_desc, title_asc"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Book).options(
        joinedload(Book.offers).joinedload(BookOffer.store),
        joinedload(Book.publisher)
    )

    # Filtro de texto (q)
    if q and q.strip():
        search_term = q.strip()
        norm_term = f"%{normalize_for_search(search_term)}%"
        # Búsqueda por ISBN exacto o coincidencia difusa en título/autor
        query = query.filter(
            or_(
                Book.isbn.ilike(f"%{search_term}%"),
                func.unaccent(func.lower(Book.title)).ilike(norm_term),
                func.unaccent(func.lower(Book.author)).ilike(norm_term),
                func.unaccent(func.lower(Book.publisher_name)).ilike(norm_term)
            )
        )

    # Filtro por editorial
    if publisher_id:
        query = query.filter(Book.publisher_id == publisher_id)

    # Filtro por tienda o ciudad o stock
    if store_id or city or in_stock_only or max_price:
        query = query.join(Book.offers).join(BookOffer.store)
        if store_id:
            query = query.filter(BookOffer.store_id == store_id)
        if city:
            query = query.filter(Store.city.ilike(f"%{city}%"))
        if in_stock_only:
            query = query.filter(BookOffer.is_in_stock == True)
        if max_price:
            query = query.filter(BookOffer.price_bob <= Decimal(str(max_price)))

    total_count = query.distinct().count()
    books = query.distinct().offset(offset).limit(limit).all()

    results = []
    for b in books:
        # Formatear ofertas ordenadas por menor precio
        sorted_offers = sorted(b.offers, key=lambda o: (not o.is_in_stock, o.price_bob))
        
        offers_out = [
            OfferOut(
                offer_id=o.offer_id,
                store_id=o.store_id,
                store_name=o.store.name if o.store else "Tienda",
                store_slug=o.store.slug if o.store else "",
                store_city=o.store.city if o.store else "",
                price_bob=float(o.price_bob),
                is_in_stock=o.is_in_stock,
                stock_label=o.stock_label or ("En stock" if o.is_in_stock else "Agotado"),
                product_url=o.product_url
            )
            for o in sorted_offers
        ]

        best_price = offers_out[0].price_bob if offers_out else None
        has_stock = any(o.is_in_stock for o in offers_out)

        results.append(
            BookSummaryOut(
                book_id=b.book_id,
                title=b.title,
                author=b.author,
                isbn=b.isbn,
                publisher_name=b.publisher_name,
                cover_image_url=b.cover_image_url,
                synopsis=b.synopsis,
                best_price_bob=best_price,
                offers_count=len(offers_out),
                available_in_stock=has_stock,
                offers=offers_out
            )
        )

    # Ordenamiento en Python para campos computados
    if sort == "price_asc":
        results.sort(key=lambda x: (x.best_price_bob is None, x.best_price_bob or 0))
    elif sort == "price_desc":
        results.sort(key=lambda x: (x.best_price_bob is None, -(x.best_price_bob or 0)))
    elif sort == "title_asc":
        results.sort(key=lambda x: x.title.lower())

    return BookSearchResponse(
        total=total_count,
        limit=limit,
        offset=offset,
        results=results
    )

@router.get("/{book_id}", response_model=BookSummaryOut)
def get_book_details(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).options(
        joinedload(Book.offers).joinedload(BookOffer.store)
    ).filter(Book.book_id == book_id).first()

    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")

    sorted_offers = sorted(book.offers, key=lambda o: (not o.is_in_stock, o.price_bob))
    offers_out = [
        OfferOut(
            offer_id=o.offer_id,
            store_id=o.store_id,
            store_name=o.store.name if o.store else "Tienda",
            store_slug=o.store.slug if o.store else "",
            store_city=o.store.city if o.store else "",
            price_bob=float(o.price_bob),
            is_in_stock=o.is_in_stock,
            stock_label=o.stock_label or ("En stock" if o.is_in_stock else "Agotado"),
            product_url=o.product_url
        )
        for o in sorted_offers
    ]

    return BookSummaryOut(
        book_id=book.book_id,
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        publisher_name=book.publisher_name,
        cover_image_url=book.cover_image_url,
        synopsis=book.synopsis,
        best_price_bob=offers_out[0].price_bob if offers_out else None,
        offers_count=len(offers_out),
        available_in_stock=any(o.is_in_stock for o in offers_out),
        offers=offers_out
    )
