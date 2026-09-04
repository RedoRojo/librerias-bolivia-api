from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.store import Store
from app.models.offer import BookOffer
from pydantic import BaseModel

router = APIRouter(prefix="/stores", tags=["Stores"])

class StoreOut(BaseModel):
    store_id: int
    name: str
    slug: str
    city: Optional[str]
    website_url: str
    cms_type: str
    is_publisher_store: bool
    total_books_in_stock: int

@router.get("", response_model=List[StoreOut])
def list_stores(db: Session = Depends(get_db)):
    stores = db.query(Store).filter(Store.is_active == True).all()
    results = []
    for s in stores:
        in_stock_cnt = db.query(func.count(BookOffer.offer_id)).filter(
            BookOffer.store_id == s.store_id,
            BookOffer.is_in_stock == True
        ).scalar() or 0
        
        results.append(
            StoreOut(
                store_id=s.store_id,
                name=s.name,
                slug=s.slug,
                city=s.city,
                website_url=s.website_url,
                cms_type=s.cms_type,
                is_publisher_store=s.is_publisher_store,
                total_books_in_stock=in_stock_cnt
            )
        )
    return results
