from typing import List, Optional
import os
import logging
import numpy as np

from models.product import Product
from services.vector_store import InMemoryVectorStore
from utils.helpers import normalize_text

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: Optional[str] = None):
        # default model dim for all-MiniLM-L6-v2 is 384
        self.dim = 384
        self.store = InMemoryVectorStore(dim=self.dim)
        self.model = None
        # try to import sentence_transformers lazily
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name or "sentence-transformers/all-MiniLM-L6-v2")
            self.dim = self.model.get_sentence_embedding_dimension()
            logger.info("Loaded sentence-transformers model: %s", model_name)
        except Exception:
            logger.warning("sentence-transformers not available, using random fallback embeddings")

    def _embed_text(self, text: str) -> List[float]:
        text = normalize_text(text or "")
        if self.model:
            vec = self.model.encode(text).tolist()
            return vec
        # fallback deterministic pseudo-embedding using hashing
        rng = np.random.RandomState(abs(hash(text)) % (2 ** 32))
        return rng.rand(self.dim).tolist()

    def upsert_product(self, product: Product):
        base = f"{product.title} {product.description or ''} {product.category or ''}"
        vec = self._embed_text(base)
        self.store.upsert(product.id, vec, metadata=product.dict())

    def get_embedding(self, product_id: str):
        meta, vec = self.store.get(product_id)
        return vec

    def search_similar(self, product_id: str, k: int = 5):
        vec = self.get_embedding(product_id)
        if vec is None:
            return []
        return self.store.search(vec, k=k)
