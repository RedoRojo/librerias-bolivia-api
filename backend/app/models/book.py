from sqlalchemy import Column, Integer, BigInteger, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

IdType = BigInteger().with_variant(Integer, "sqlite")

class Book(Base):
    __tablename__ = "books"

    book_id = Column(IdType, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False, index=True)
    author = Column(Text, nullable=True, index=True)
    isbn = Column(Text, nullable=True, index=True)
    publisher_id = Column(IdType, ForeignKey("publishers.publisher_id", ondelete="SET NULL"), nullable=True, index=True)
    publisher_name = Column(Text, nullable=False, default="No especificada")
    publisher_source = Column(Text, nullable=False, default="unknown")
    cover_image_url = Column(Text, nullable=True)
    synopsis = Column(Text, nullable=True)
    pages = Column(Integer, nullable=True)
    year_published = Column(Integer, nullable=True)
    needs_enrichment = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    publisher = relationship("Publisher", back_populates="books")
    offers = relationship("BookOffer", back_populates="book", cascade="all, delete-orphan")
