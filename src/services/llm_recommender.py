from typing import List, Optional
import json
import re
import logging
from decimal import Decimal
from sqlalchemy.orm import Session
from src.models.product import Product
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace


def _build_prompt(target: Product, candidates: List[Product], top_k: int = 5) -> str:
    candidates_str = []
    for p in candidates:
        candidates_str.append(
            f"- id: {p.id}\n  name: {p.name}\n  description: {p.description or ''}\n  category: {p.category or ''}\n  price: {float(p.price) if p.price is not None else 'None'}\n"
        )

    prompt = (
        "Tu es un moteur de recommandation produit.\n"
        "Voici le produit consulté :\n"
        f"id: {target.id}\nname: {target.name}\ndescription: {target.description or ''}\ncategory: {target.category or ''}\nprice: {float(target.price) if target.price is not None else 'None'}\n\n"
        "Voici une liste de produits candidats :\n"
        + "\n".join(candidates_str)
        + "\nTa tâche est de renvoyer les 5 produits les plus similaires en tenant compte de :\n"
        "- usage\n- style\n- cible utilisateur\n- gamme de prix\n- intention d’achat\n\n"
        "Réponds au format JSON:\n"
        "[\n  {\"product_id\": \"...\", \"score\": 0.0, \"reason\": \"...\"},\n  ...\n]\n"
    )
    return prompt


def _extract_json(text: str) -> Optional[str]:
    # Try direct parse
    try:
        json.loads(text)
        return text
    except Exception:
        pass

    # Find first JSON array in text
    m = re.search(r"(\[\s*\{[\s\S]*?\}\s*\])", text)
    if m:
        return m.group(1)

    # Fallback: try to find between first '[' and last ']'
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
    Recommande des produits en s'appuyant sur un LLM (Llama-3.1-8B-Instruct).

    - Récupère le produit cible depuis la base
    - Pré-filtre des candidats (même catégorie, gamme de prix +/-20%)
    - Construit le prompt et appelle le modèle via LangChain
    - Parse la réponse JSON et renvoie la liste d'IDs triés
    """

    # 1) Récupère le produit cible
    target = db.query(Product).filter(Product.id == product_id).first()
    if not target:
        logging.warning("Product with id %s not found", product_id)
        return []

    # 2) Pré-filtre des candidats: même catégorie et gamme de prix +/-20%
    price_val = None
    try:
        price_val = float(target.price) if target.price is not None else None
    except Exception:
        # If price cannot be interpreted, ignore price filter
        price_val = None

    query = db.query(Product).filter(Product.id != target.id)
    if target.category:
        query = query.filter(Product.category == target.category)

    if price_val is not None:
        min_p = Decimal(price_val) * Decimal("0.8")
        max_p = Decimal(price_val) * Decimal("1.2")
        query = query.filter(Product.price >= min_p, Product.price <= max_p)

    candidates = query.limit(candidate_limit).all()

    if not candidates:
        logging.info("No candidates found for product %s", product_id)
        return []

    # 3) Construit le prompt
    prompt = _build_prompt(target, candidates, top_k=limit)

    # 4) Appelle le modèle via LangChain -> HuggingFace
    try:
        # Create the low-level endpoint wrapper
        llm = HuggingFaceEndpoint(
            repo_id="meta-llama/Llama-3.1-8B-Instruct",
            task="text-generation",
            max_new_tokens=512,
            do_sample=False,
        )
        chat = ChatHuggingFace(llm=llm, verbose=False)

        messages = [
            ("system", "Tu es un moteur de recommandation produit."),
            ("human", prompt),
        ]

        ai_msg = chat.invoke(messages)

        # ai_msg may be an object with `.content`
        text = getattr(ai_msg, "content", None) or str(ai_msg)
    except Exception as e:
        logging.exception("LLM call failed: %s", e)
        # Fallback: return first N candidate ids
        return [str(p.id) for p in candidates[:limit]]

    # 5) Parse la réponse JSON
    json_str = _extract_json(text)
    if not json_str:
        logging.warning("No JSON found in model response. Returning candidate fallback.")
        return [str(p.id) for p in candidates[:limit]]

    try:
        parsed = json.loads(json_str)
        # Expecting a list of objects with product_id and score
        if not isinstance(parsed, list):
            logging.warning("Parsed JSON is not a list. Fallback to candidates.")
            return [str(p.id) for p in candidates[:limit]]

        # Build list of tuples (id, score)
        results = []
        for item in parsed:
            pid = item.get("product_id") or item.get("productId") or item.get("id")
            try:
                score = float(item.get("score", 0.0))
            except Exception:
                score = 0.0
            if pid is not None:
                results.append((str(pid), score))

        # Sort by score desc and return up to `limit` ids
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results][:limit]
    except Exception:
        logging.exception("Failed to parse JSON from model response")
        return [str(p.id) for p in candidates[:limit]]

    