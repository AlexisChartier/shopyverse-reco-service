import sys
import importlib
from decimal import Decimal

import pytest


def test_tfidf_get_similar_products(monkeypatch):
    """
    Vérifie que get_similar_products renvoie bien des produits similaires
    au produit cible, en utilisant un backend SQLite in-memory.

    On force DATABASE_URL à vide, on recharge les modules core/database
    et models/product, puis on insère quelques produits et on vérifie
    que le plus similaire est bien celui qui partage le plus de mots.
    """
    # 1) Forcer un environnement "CI" / test sans DB externe
    monkeypatch.setenv("DATABASE_URL", "")

    # 2) Nettoyer les modules déjà importés pour qu'ils relisent la config
    for m in [
        "src.core.config",
        "src.core.database",
        "src.models.product",
        "src.services.tfidf_recommender",
    ]:
        if m in sys.modules:
            del sys.modules[m]

    # 3) Réimporter les modules avec la bonne config
    db = importlib.import_module("src.core.database")
    product_mod = importlib.import_module("src.models.product")
    tfidf_mod = importlib.import_module("src.services.tfidf_recommender")

    # Sanity check : on doit être sur du SQLite (fallback)
    assert db.engine is not None
    assert db.engine.dialect.name == "sqlite"

    # 4) Créer les tables en mémoire
    db.Base.metadata.create_all(bind=db.engine)

    Session = db.SessionLocal

    # 5) Insérer quelques produits
    with Session() as session:
        p1 = product_mod.Product(
            name="Red T-Shirt",
            description="Basic red cotton t-shirt",
            category="clothes",
            price=Decimal("19.99"),
            image_url="http://example.com/red1.png",
        )
        p2 = product_mod.Product(
            name="Red Cotton T-Shirt",
            description="Premium red cotton t-shirt for men",
            category="clothes",
            price=Decimal("24.99"),
            image_url="http://example.com/red2.png",
        )
        p3 = product_mod.Product(
            name="Coffee Mug",
            description="White ceramic coffee mug",
            category="kitchen",
            price=Decimal("9.99"),
            image_url="http://example.com/mug.png",
        )
        session.add_all([p1, p2, p3])
        session.commit()

        # On rafraîchit pour récupérer les IDs
        session.refresh(p1)
        session.refresh(p2)
        session.refresh(p3)

        # 6) Appeler le moteur TF-IDF sur p1
        similar = tfidf_mod.get_similar_products(session, p1, top_n=2)

        # On s'attend à ce que le produit le plus similaire soit p2 (le t-shirt),
        # et surtout PAS p3 (la tasse).
        ids = {str(p.id) for p in similar}

        assert str(p2.id) in ids, "Le t-shirt similaire devrait être dans les recommandations"
        assert str(p3.id) not in ids, "La tasse ne devrait pas être dans les top recommandations"
        assert len(similar) >= 1