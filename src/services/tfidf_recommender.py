# src/services/tfidf_recommender.py

from typing import List
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.models.product import Product


def _product_text(p: Product) -> str:
    """Concatène name + description pour créer un texte d'entrée TF-IDF."""
    name = p.name or ""
    desc = p.description or ""
    return f"{name}. {desc}"


def get_similar_products(
    db: Session,
    target_product: Product,
    top_n: int = 5,
) -> List[Product]:
    """
    Recommandations basées sur TF-IDF + similarité cosinus.

    Étapes :
    - récupère tous les produits de la même catégorie (ou tous si aucune)
    - construit un corpus TF-IDF
    - calcule les similarités
    - renvoie les produits les plus similaires
    """

    if not target_product:
        return []

    # 1) Préfiltrage : même catégorie si dispo
    query = db.query(Product).filter(Product.id != target_product.id)

    if target_product.category:
        query = query.filter(Product.category == target_product.category)

    candidates = query.all()

    if not candidates:
        return []

    # 2) Construire le corpus TF-IDF
    docs = [_product_text(target_product)] + [_product_text(p) for p in candidates]

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(docs)

    # 3) Similarités
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    # 4) Trier les candidats selon la similarité
    scored = list(zip(candidates, similarities))
    scored.sort(key=lambda x: x[1], reverse=True)

    top_products = scored[:top_n]

    # 5) Récupérer les `top_ids` pour la requête SQL (normalisation UUID obligatoire)
    top_ids = [str(product.id) for product, _ in top_products]

    normalized_ids = []
    for pid in top_ids:
        # SQLite n'accepte pas les strings pour UUID — convertir obligatoirement
        try:
            normalized_ids.append(UUID(str(pid)))
        except Exception:
            # Si un id est invalide → on ignore
            continue

    if not normalized_ids:
        return []

    # 6) Renvoyer les produits dans l'ordre correct
    results = db.query(Product).filter(Product.id.in_(normalized_ids)).all()

    # On préserve l'ordre (SQL ne le garantit pas)
    id_to_product = {str(p.id): p for p in results}
    ordered = [id_to_product[str(pid)] for pid in normalized_ids if str(pid) in id_to_product]

    return ordered