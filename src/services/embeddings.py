from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import uuid
from src.core.config import settings

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
qdrant = QdrantClient(host="qdrant", port=6333)

# Créer la collection si elle n'existe pas
qdrant.recreate_collection(
    collection_name="products",
    vectors_config=VectorParams(
        size=384,
        distance=Distance.COSINE
    )
)

def add_product_embedding(product_id, text: str):
    vector = model.encode(text).tolist()
    print("VECTOR SIZE:", len(vector), "VECTOR SAMPLE:", vector[:5])
    qdrant.upsert(
        collection_name="products",
        points=[PointStruct(id=str(uuid.uuid4()), vector=vector, payload={"product_id": str(product_id)})]
    )

def find_similar_products(product_id: str, limit: int = 5):
    # Récupérer le vecteur du produit
    results = qdrant.scroll(collection_name="products", scroll_filter={"must": [{"key": "product_id", "match": {"value": product_id}}]})
    if not results[0]:
        return []

    vector = results[0][0].vector
    # Rechercher les vecteurs les plus similaires
    hits = qdrant.search(collection_name="products", query_vector=vector, limit=limit)
    return [hit.payload["product_id"] for hit in hits if hit.payload["product_id"] != product_id]
