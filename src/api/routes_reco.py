from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.product import Product
# from src.services.embeddings import add_product_embedding
from src.services.llm_recommender import recommend_products
from src.schemas.product import ProductCreate, ProductResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    # créer embedding et stocker dans Qdrant
    # add_product_embedding(new_product.id, f"{new_product.name} {new_product.description}")

    return new_product

@router.get("/recommendations", response_model=list[ProductResponse])
def get_recommendations(product_id: str, db: Session = Depends(get_db)):
    """
    Reco endpoint now driven by an LLM-based recommender.

    Flow:
    - récupère le produit cible
    - préfiltre candidats (dans le service)
    - envoie au LLM qui renvoie une liste triée d'IDs
    - retourne les produits correspondants
    """
    try:
        recommended_ids = recommend_products(db, product_id, limit=5, candidate_limit=30)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        # e.g. missing HF token or langchain not installed
        raise HTTPException(status_code=500, detail=str(e))

    products = db.query(Product).filter(Product.id.in_(recommended_ids)).all()
    if not products:
        raise HTTPException(status_code=404, detail="No recommendations found")
    # Preserve ordering from recommended_ids
    id_to_product = {str(p.id): p for p in products}
    ordered = [id_to_product[rid] for rid in recommended_ids if rid in id_to_product]
    return ordered

@router.get("/products/list")
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()
