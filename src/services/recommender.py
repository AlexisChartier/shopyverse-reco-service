from typing import List
from services.embeddings import EmbeddingService


class Recommender:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    def recommend_similar(self, product_id: str, k: int = 5) -> List[dict]:
        results = self.embedding_service.search_similar(product_id, k=k + 1)
        # filter out the query product itself if present
        filtered = [r for r in results if r[0] != product_id][:k]
        return [{"product_id": pid, "score": float(score)} for pid, score in filtered]

    def recommend_contextual(self, user_context: dict, k: int = 5) -> List[dict]:
        # Placeholder: integrate LangChain agent here to combine context and vector search
        # For now use simple heuristics: if recent_product in context, return similar
        recent = user_context.get("recent_product_id")
        if recent:
            return self.recommend_similar(recent, k=k)
        return []
