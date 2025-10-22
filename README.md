# shopyverse-reco-service

Prototype micro-service for product recommendations. Includes:

- FastAPI HTTP API
- In-memory vector store with optional sentence-transformers embeddings
- Recommender service and LangChain agent stub

Quick start

1. Create a virtualenv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the app:

```bash
uvicorn src.main:app --reload
```

3. Ingest products:

POST /api/products with JSON body {id, title, description}

4. Get recommendations:

GET /api/recommendations?product_id=p1&k=5

Notes and next steps

- Replace InMemoryVectorStore with FAISS/Qdrant/Chroma adapter in `src/services/vector_store.py`.
- Replace embedding fallback with production HF model; set `HF_MODEL` in env.
- Implement `src/agents/langchain_agent.py` using LangChain's Agent and Tools for contextual recommendations.
- Add persistent product metadata in Postgres and integrate via ProductDBTool.

# reco service
