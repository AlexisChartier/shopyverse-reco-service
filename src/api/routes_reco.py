from fastapi import APIRouter, HTTPException, Query
from typing import List

from api import schemas
from models.product import Product
from services.embeddings import EmbeddingService
from services.recommender import Recommender

router = APIRouter()

# simple in-memory instances for this prototype
embedding_svc = EmbeddingService()
recommender = Recommender(embedding_svc)


@router.post("/products", status_code=201)
def add_product(product: schemas.ProductIn):
    p = Product(**product.dict())
    # store embedding and metadata
    try:
        embedding_svc.upsert_product(p)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok", "id": p.id}


@router.get("/recommendations", response_model=schemas.RecommendationsOut)
def get_recommendations(product_id: str = Query(..., description="Product id to query"), k: int = 5):
    recs = recommender.recommend_similar(product_id=product_id, k=k)
    return {"query_product": product_id, "recommendations": recs}
