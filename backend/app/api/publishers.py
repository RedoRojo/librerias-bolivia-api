from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.publisher import Publisher
from app.models.book import Book
from pydantic import BaseModel

router = APIRouter(prefix="/publishers", tags=["Publishers"])

class PublisherOut(BaseModel):
    publisher_id: int
    name: str
    slug: str
    country: Optional[str]
    total_books: int

@router.get("", response_model=List[PublisherOut])
def list_publishers(db: Session = Depends(get_db)):
    publishers = db.query(Publisher).order_by(Publisher.name.asc()).all()
    results = []
    for p in publishers:
        books_cnt = db.query(func.count(Book.book_id)).filter(
            Book.publisher_id == p.publisher_id
        ).scalar() or 0
        
        results.append(
            PublisherOut(
                publisher_id=p.publisher_id,
                name=p.name,
                slug=p.slug,
                country=p.country,
                total_books=books_cnt
            )
        )
    return results
