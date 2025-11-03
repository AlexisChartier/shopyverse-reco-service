from sqlalchemy import Column, String, Text, Numeric, TIMESTAMP, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from src.core.database import Base
import uuid

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    price = Column(Numeric(10, 2))
    image_url = Column(Text)
    merchant_id = Column(UUID(as_uuid=True)) # Pas sur, peut etre que le site_id suffit ?
    site_id = Column(UUID(as_uuid=True))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
