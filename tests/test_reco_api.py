from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ingest_and_recommend():
    p1 = {"id": "p1", "title": "Sneakers AirRun", "description": "sport shoes"}
    p2 = {"id": "p2", "title": "Sport Socks", "description": "breathable socks"}
    r = client.post("/api/products", json=p1)
    assert r.status_code == 201
    r = client.post("/api/products", json=p2)
    assert r.status_code == 201

    r = client.get("/api/recommendations", params={"product_id": "p1", "k": 1})
    assert r.status_code == 200
    data = r.json()
    assert data["query_product"] == "p1"
    assert "recommendations" in data
