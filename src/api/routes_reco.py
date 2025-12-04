from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from src.core.database import SessionLocal
from src.models.product import Product
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
    return new_product


@router.get("/products/list")
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@router.get("/recommendations", response_model=list[ProductResponse])
def get_recommendations(product_id: str, db: Session = Depends(get_db)):
    """
    Endpoint de reco hybride :
    - TF-IDF pour pré-sélectionner des candidats
    - LLM HuggingFace pour reranker (si dispo)
    - Fallback TF-IDF si le LLM échoue
    """

    # 1) Appel du moteur de reco hybride (gère déjà les ValueError utiles)
    try:
        recommended_ids = recommend_products(
            db, product_id, limit=5, candidate_limit=30
        )
    except ValueError as e:
        # Par ex : UUID invalide, produit non trouvé
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # Si tu veux remonter un cas particulier
        raise HTTPException(status_code=500, detail=str(e))

    if not recommended_ids:
        raise HTTPException(status_code=404, detail="No recommendations found")

    # 2) Conversion des IDs string -> UUID pour SQLAlchemy (type UUID en base)
    uuid_ids: list[uuid.UUID] = []
    for rid in recommended_ids:
        try:
            uuid_ids.append(uuid.UUID(rid))
        except ValueError:
            # Sécurité : on ignore un ID que le LLM aurait inventé ou mal formé
            continue

    if not uuid_ids:
        raise HTTPException(status_code=404, detail="No valid recommendations")

    # 3) Récupération des produits en base
    products = db.query(Product).filter(Product.id.in_(uuid_ids)).all()
    if not products:
        raise HTTPException(status_code=404, detail="No recommendations in database")

    # 4) On conserve l'ordre défini par recommended_ids
    id_to_product = {str(p.id): p for p in products}
    ordered = [id_to_product[rid] for rid in recommended_ids if rid in id_to_product]

    return ordered