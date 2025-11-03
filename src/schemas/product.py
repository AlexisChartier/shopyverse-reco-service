from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ProductCreate(BaseModel):
    name: str
    description: Optional[str]
    category: Optional[str]
    price: float
    image_url: Optional[str]
    merchant_id: Optional[UUID]
    site_id: Optional[UUID]

class ProductResponse(ProductCreate):
    id: UUID
