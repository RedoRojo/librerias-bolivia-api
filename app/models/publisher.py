from sqlalchemy import Column, Integer, BigInteger, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

IdType = BigInteger().with_variant(Integer, "sqlite")

class Publisher(Base):
    __tablename__ = "publishers"

    publisher_id = Column(IdType, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True, index=True)
    slug = Column(Text, nullable=False, unique=True, index=True)
    country = Column(Text, default="Bolivia")
    website_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    books = relationship("Book", back_populates="publisher")
