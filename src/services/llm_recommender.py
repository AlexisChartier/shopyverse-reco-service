from typing import List, Optional
import os
import json
import re
import uuid

from sqlalchemy.orm import Session

from src.models.product import Product
from src.services.tfidf_recommender import get_similar_products

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _build_prompt(target: Product, candidates: List[Product], top_k: int = 5) -> str:
    """Construit le prompt envoyé au LLM pour reranker les candidats."""

    candidates_str = []
    for p in candidates:
        candidates_str.append(
            f"- id: {p.id}\n"
            f"  name: {p.name}\n"
            f"  description: {p.description or ''}\n"
            f"  category: {p.category or ''}\n"
            f"  price: {float(p.price) if p.price is not None else 'None'}\n"
        )

    prompt = (
        "Tu es un moteur de recommandation produit.\n"
        "Voici le produit consulté :\n"
        f"id: {target.id}\n"
        f"name: {target.name}\n"
        f"description: {target.description or ''}\n"
        f"category: {target.category or ''}\n"
        f"price: {float(target.price) if target.price is not None else 'None'}\n\n"
        "Voici une liste de produits candidats :\n"
        + "\n".join(candidates_str)
        + "\nTa tâche est de renvoyer les produits les plus similaires en tenant compte de :\n"
        "- usage\n- style\n- cible utilisateur\n- gamme de prix\n- intention d’achat\n\n"
        "Réponds au format JSON strict, sous la forme :\n"
        "[\n"
        '  {"product_id": "...", "score": 0.0, "reason": "..."},\n'
        "  ...\n"
        "]\n"
    )
    return prompt


def _extract_json(text: str) -> Optional[str]:
    """Essaie d'extraire un tableau JSON depuis une réponse texte du LLM."""

    # 1) Essai direct
    try:
        json.loads(text)
        return text
    except Exception:
        pass

    # 2) Cherche le premier tableau JSON dans le texte
    m = re.search(r"(\[\s*\{[\s\S]*?\}\s*\])", text)
    if m:
        return m.group(1)

    # 3) Fallback grossier : entre le premier '[' et le dernier ']'
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            return None

    return None


def recommend_products(
    db: Session,
    product_id: str,
    limit: int = 5,
    candidate_limit: int = 30,
) -> List[str]:
    """
    Recommandation HYBRIDE :

    1. Récupère le produit cible depuis la base.
    2. Utilise TF-IDF pour pré-sélectionner les candidats.
    3. Si possible → le LLM rerank la liste.
    4. En cas d’échec → fallback TF-IDF.
    """

    logging.info("🔎 [HYBRID-RECO] Requête de reco reçue pour product_id=%s", product_id)

    # 1) Vérif / conversion de l'UUID
    try:
        target_uuid = uuid.UUID(product_id)
        logging.info("📌 [HYBRID-RECO] UUID valide → %s", target_uuid)
    except ValueError:
        logging.error("❌ [HYBRID-RECO] UUID invalide pour product_id=%s", product_id)
        raise ValueError("product_id must be a valid UUID string")

    target = db.query(Product).filter(Product.id == target_uuid).first()
    if not target:
        logging.error("❌ [HYBRID-RECO] Produit introuvable en base : %s", product_id)
        raise ValueError(f"Product with id {product_id} not found")

    # 2) Pré-filtrage via TF-IDF
    logging.info("🧮 [TF-IDF] Pré-sélection des %s meilleurs candidats…", candidate_limit)

    candidates: List[Product] = get_similar_products(
        db, target, top_n=candidate_limit
    )

    if not candidates:
        logging.warning("⚠️ [TF-IDF] Aucun candidat trouvé → retour list vide.")
        return []

    logging.info("✅ [TF-IDF] %s candidats trouvés", len(candidates))

    # Si moins de candidats que limit
    if len(candidates) < limit:
        limit = len(candidates)

    # 3) Prompt pour le LLM
    prompt = _build_prompt(target, candidates, top_k=limit)

    # 4) Appel LLM HuggingFace via LangChain
    try:
        from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

        if not os.getenv("HUGGINGFACEHUB_API_TOKEN"):
            logging.warning("⚠️ [LLM] Aucun token HF → fallback TF-IDF activé.")
            raise RuntimeError("HUGGINGFACEHUB_API_TOKEN is not set")

        logging.info("🤖 [LLM] Appel du modèle HuggingFace pour reranking…")

        llm = HuggingFaceEndpoint(
            repo_id="HuggingFaceH4/zephyr-7b-beta",            
            task="text-generation",
            max_new_tokens=512,
            do_sample=False,
        )
        chat = ChatHuggingFace(llm=llm, verbose=True)

        messages = [
            ("system", "Tu es un moteur de recommandation produit."),
            ("human", prompt),
        ]

        ai_msg = chat.invoke(messages)
        text = getattr(ai_msg, "content", None) or str(ai_msg)

    except Exception as e:
        logging.exception("❌ [LLM] Échec de l'appel LLM → fallback TF-IDF : %s", e)
        return [str(p.id) for p in candidates[:limit]]

    # 5) Parsing du JSON
    logging.info("🧩 [LLM] Tentative de parsing du JSON renvoyé…")

    json_str = _extract_json(text)
    if not json_str:
        logging.warning(
            "⚠️ [LLM] Aucun JSON détecté → fallback TF-IDF."
        )
        return [str(p.id) for p in candidates[:limit]]

    try:
        parsed = json.loads(json_str)

        if not isinstance(parsed, list):
            logging.warning("⚠️ [LLM] JSON incorrect → fallback TF-IDF.")
            return [str(p.id) for p in candidates[:limit]]

        results: list[tuple[str, float]] = []

        for item in parsed:
            pid = item.get("product_id") or item.get("productId") or item.get("id")
            score = float(item.get("score", 0.0)) if item.get("score") else 0.0

            if pid:
                results.append((str(pid), score))

        results.sort(key=lambda x: x[1], reverse=True)

        candidate_ids = {str(p.id) for p in candidates}
        filtered = [r for r in results if r[0] in candidate_ids]

        if not filtered:
            logging.info(
                "⚠️ [LLM] Aucune correspondance LLM dans les candidats → fallback TF-IDF."
            )
            return [str(p.id) for p in candidates[:limit]]

        logging.info("✅ [LLM] Reranking LLM utilisé avec succès 🎉")

        return [r[0] for r in filtered][:limit]

    except Exception as e:
        logging.exception("❌ [LLM] Erreur parsing JSON → fallback TF-IDF : %s", e)
        return [str(p.id) for p in candidates[:limit]]