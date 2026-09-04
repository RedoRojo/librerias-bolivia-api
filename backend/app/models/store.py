from sqlalchemy import Column, Integer, BigInteger, Text, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

IdType = BigInteger().with_variant(Integer, "sqlite")

class Store(Base):
    __tablename__ = "stores"

    store_id = Column(IdType, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    slug = Column(Text, nullable=False, unique=True, index=True)
    city = Column(Text, nullable=True)
    website_url = Column(Text, nullable=False)
    logo_url = Column(Text, nullable=True)
    has_delivery = Column(Boolean, default=True, nullable=False)
    cms_type = Column(Text, nullable=False)  # 'woocommerce', 'shopify', 'wix', 'custom'
    is_publisher_store = Column(Boolean, default=False, nullable=False)
    default_publisher_name = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    offers = relationship("BookOffer", back_populates="store", cascade="all, delete-orphan")
