from sqlalchemy import Column, Integer, BigInteger, Text, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.core.database import Base

IdType = BigInteger().with_variant(Integer, "sqlite")

class BookOffer(Base):
    __tablename__ = "book_offers"

    offer_id = Column(IdType, primary_key=True, autoincrement=True)
    book_id = Column(IdType, ForeignKey("books.book_id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(IdType, ForeignKey("stores.store_id", ondelete="RESTRICT"), nullable=False, index=True)
    price_bob = Column(Numeric(10, 2), nullable=False)
    is_in_stock = Column(Boolean, default=True, nullable=False)
    stock_label = Column(Text, default="En stock", nullable=True)
    product_url = Column(Text, nullable=False)
    raw_sku = Column(Text, nullable=True)
    raw_title = Column(Text, nullable=True)
    last_checked_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    book = relationship("Book", back_populates="offers")
    store = relationship("Store", back_populates="offers")

    __table_args__ = (
        UniqueConstraint("book_id", "store_id", name="uq_book_store"),
    )
