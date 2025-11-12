# from sentence_transformers import SentenceTransformer
# from qdrant_client import QdrantClient, models
# from qdrant_client.models import PointStruct, VectorParams, Distance
# import uuid
# from src.core.config import settings

# model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
# qdrant = QdrantClient(host="qdrant", port=6333)

# # Créer la collection si elle n'existe pas
# try:
#     qdrant.get_collection("products")
# except Exception:
#     qdrant.create_collection(
#         collection_name="products",
#         vectors_config=VectorParams(
#             size=384,
#             distance=Distance.COSINE
#         )
#     )

# def add_product_embedding(product_id, text: str):
#     vector = model.encode(text).tolist()
#     # print("VECTOR SIZE:", len(vector), "VECTOR SAMPLE:", vector[:5])
#     qdrant.upsert(
#         collection_name="products",
#         points=[
#             PointStruct(
#                 id=str(product_id), 
#                 vector=vector, 
#                 payload={"product_id": str(product_id)}
#             )
#         ]
#     )

# def find_similar_products(product_id: str, limit: int = 5):
#     """
#     Trouve des produits similaires en utilisant l'API de recommandation de Qdrant.

#     - product_id: id du produit source (utilisé comme exemple positif)
#     - limit: nombre maximum de résultats retournés
#     - strategy: stratégie de recommandation (ex: "best_score", "average_vector", ...)

#     Retourne une liste d'ids (strings) des produits similaires, sans inclure l'id source.
#     """

#     # Construire une RecommendQuery typée (évite l'erreur "Unsupported query type: dict")

#     recommend_input = models.RecommendInput(
#         positive=[str(product_id)],
#         strategy=models.RecommendStrategy.BEST_SCORE,
#     )

#     query = models.RecommendQuery(recommend=recommend_input)

#     # Filtre pour exclure explicitement le produit source
#     query_filter = models.Filter(
#         must_not=[
#             models.FieldCondition(
#                 key="product_id",
#                 match=models.MatchValue(value=str(product_id)),
#             )
#         ]
#     )

#     # Certains serveurs Qdrant plus anciens n'implémentent pas l'endpoint unifié
#     # POST /collections/{name}/points/query (retourne 404). Utilisons l'endpoint
#     # dédié /collections/{name}/points/recommend via le client HTTP bas-niveau.
#     try:
#         recommend_request = models.RecommendRequest(recommend=recommend_input, limit=limit)
#         http_resp = qdrant.http.search_api.recommend_points(
#             collection_name="products",
#             recommend_request=recommend_request,
#         )
#         # Le wrapper HTTP renvoie un InlineResponse20017 avec .result = List[ScoredPoint]
#         res = http_resp.result or []
#     except Exception:
#         # Fallback: si l'appel direct échoue, retomber sur l'endpoint unifié (peut lever 404)
#         res = qdrant.query_points(
#             collection_name="products",
#             query=query,
#             query_filter=query_filter,
#             limit=limit,
#         )

#     # Le client peut renvoyer soit un dict JSON-like, soit un objet with .result, ou directement
#     # une liste d'objets. Normaliser en liste Python simple.
#     if isinstance(res, dict):
#         results = res.get("result", [])
#     elif hasattr(res, "result"):
#         results = getattr(res, "result") or []
#     else:
#         results = res or []

#     similar_ids = []
#     for item in results:
#         # item peut être un dict {'id': ...} ou un objet avec attribut .id
#         if isinstance(item, dict):
#             pid = item.get("id")
#         else:
#             pid = getattr(item, "id", None)

#         if pid is None:
#             # certains formats encapsulent le point sous 'point' ou 'payload'
#             if isinstance(item, dict):
#                 point = item.get("point") or item.get("payload")
#                 if isinstance(point, dict):
#                     pid = point.get("id") or point.get("payload", {}).get("product_id")

#         if pid is None:
#             continue

#         pid_str = str(pid)
#         if pid_str == str(product_id):
#             continue

#         similar_ids.append(pid_str)

#     return similar_ids[:limit]
