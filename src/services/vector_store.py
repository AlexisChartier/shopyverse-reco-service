from typing import Dict, List, Tuple
from utils.helpers import cosine_sim


class InMemoryVectorStore:
    def __init__(self, dim: int = 384):
        self.dim = dim
        self.vectors: Dict[str, List[float]] = {}
        self.metadata: Dict[str, dict] = {}

    def upsert(self, id: str, vector: List[float], metadata: dict = None):
        self.vectors[id] = vector
        self.metadata[id] = metadata or {}

    def search(self, vector: List[float], k: int = 5) -> List[Tuple[str, float]]:
        # naive linear scan
        scores = []
        for pid, vec in self.vectors.items():
            score = cosine_sim(vector, vec)
            scores.append((pid, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def get(self, id: str):
        return self.metadata.get(id), self.vectors.get(id)
