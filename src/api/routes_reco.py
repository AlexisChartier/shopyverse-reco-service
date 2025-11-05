from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.product import Product
from src.services.embeddings import add_product_embedding, find_similar_products
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
    add_product_embedding(new_product.id, f"{new_product.name} {new_product.description}")

    return new_product

@router.get("/recommendations", response_model=list[ProductResponse])
def get_recommendations(product_id: str, db: Session = Depends(get_db)):
    similar_ids = find_similar_products(product_id)
    products = db.query(Product).filter(Product.id.in_(similar_ids)).all()
    if not products:
        raise HTTPException(status_code=404, detail="No recommendations found")
    return products

@router.get("/products/list")
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()
