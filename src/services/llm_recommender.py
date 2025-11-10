from typing import List, Optional
import os
import json
import re

from sqlalchemy.orm import Session

from src.models.product import Product

try:
    from langchain.llms import HuggingFaceHub
    # LangSmith tracer is optional
    try:
        from langchain.callbacks.tracers import LangSmithTracer
    except Exception:
        LangSmithTracer = None
except Exception:
    # If langchain not installed, we will raise at runtime when used
    HuggingFaceHub = None
    LangSmithTracer = None


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
    Recommande des produits en s'appuyant sur un LLM (Llama-3.1-8B-Instruct via HuggingFaceHub).

    - Récupère le produit cible depuis la base
    - Pré-filtre des candidats (même catégorie, gamme de prix +/-20%)
    - Construit le prompt et appelle le modèle via LangChain
    - Parse la réponse JSON et renvoie la liste d'IDs triés
    """

    if HuggingFaceHub is None:
        raise RuntimeError("langchain is required for LLM recommender. Install requirements and try again.")

    # fetch target product
    target = db.query(Product).filter(Product.id == product_id).one_or_none()
    if target is None:
        raise ValueError(f"Product {product_id} not found")

    # Simple prefilter: same category + price window
    q = db.query(Product).filter(Product.id != product_id)
    if target.category:
        q = q.filter(Product.category == target.category)

    candidates = q.limit(candidate_limit).all()

    # If category filter returns too few, widen to any product
    if not candidates:
        candidates = db.query(Product).filter(Product.id != product_id).limit(candidate_limit).all()

    # Build prompt
    prompt = _build_prompt(target, candidates, top_k=limit)

    # Instantiate LLM (HuggingFaceHub) - expects HUGGINGFACEHUB_API_TOKEN in env
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not hf_token:
        raise RuntimeError("HUGGINGFACEHUB_API_TOKEN not set. Set it to call the Llama model via HuggingFace Inference API.")

    # Using meta-llama Llama-3.1-8B-Instruct model name on HF - may vary if your deployment differs
    llm = HuggingFaceHub(repo_id="meta-llama/Llama-3.1-8b-instruct", huggingfacehub_api_token=hf_token, model_kwargs={"temperature":0.0, "max_length":1024})

    # Optional LangSmith tracer
    tracer = None
    langsmith_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGSMITH_API_TOKEN")
    if LangSmithTracer is not None and langsmith_key:
        try:
            tracer = LangSmithTracer()
        except Exception:
            tracer = None

    # Call the model
    if tracer is not None:
        with tracer.as_default():
            raw = llm(prompt)
    else:
        raw = llm(prompt)

    # Parse result
    json_text = _extract_json(raw)
    if not json_text:
        # If model did not return JSON, raise with raw text for debugging
        raise ValueError(f"LLM did not return valid JSON. Raw response: {raw}")

    parsed = json.loads(json_text)
    product_ids: List[str] = []
    for item in parsed:
        pid = item.get("product_id") or item.get("id")
        if pid:
            product_ids.append(str(pid))
        if len(product_ids) >= limit:
            break

    return product_ids
