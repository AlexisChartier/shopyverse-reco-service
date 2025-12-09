import sys
import importlib
from decimal import Decimal

import pytest


def test_sqlite_in_memory_used_and_product_crud(monkeypatch):
    """Force no DATABASE_URL, reload modules, create tables in-memory and test CRUD."""
    # Ensure CI-like environment: force DATABASE_URL to an empty value (falsy)
    monkeypatch.setenv("DATABASE_URL", "")

    # Remove cached modules so they pick up env change
    for m in ["src.core.config", "src.core.database", "src.models.product"]:
        if m in sys.modules:
            del sys.modules[m]

    # Import database after env change
    db = importlib.import_module("src.core.database")

    # Sanity: engine should be sqlite in-memory when DATABASE_URL not set
    assert db.engine is not None
    # dialect.name is 'sqlite' for in-memory SQLite engines
    assert db.engine.dialect.name == "sqlite"

    # Import the Product model (it imports Base from src.core.database)
    product_mod = importlib.import_module("src.models.product")

    # Create all tables on the in-memory engine
    db.Base.metadata.create_all(bind=db.engine)

    # Open a session and perform simple CRUD
    Session = db.SessionLocal
    with Session() as session:
        prod = product_mod.Product(
            name="Test product",
            description="A test",
            category="tests",
            price=Decimal("9.99"),
            image_url="http://example.com/image.png",
            merchant_id=None,
            site_id=None,
        )
        session.add(prod)
        session.commit()

        # Query back
        rows = session.query(product_mod.Product).filter_by(name="Test product").all()
        assert len(rows) == 1
        assert rows[0].description == "A test"
