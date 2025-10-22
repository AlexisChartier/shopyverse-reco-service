from pydantic import BaseModel, Field
from typing import Optional, List


class ProductIn(BaseModel):
    id: str = Field(..., description="Product unique id")
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None


class Recommendation(BaseModel):
    product_id: str
    score: float


class RecommendationsOut(BaseModel):
    query_product: str
    recommendations: List[Recommendation]
