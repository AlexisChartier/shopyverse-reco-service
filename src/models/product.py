from pydantic import BaseModel
from typing import Optional


class Product(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
