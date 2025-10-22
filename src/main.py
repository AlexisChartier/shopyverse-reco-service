from fastapi import FastAPI
from api import routes_reco

app = FastAPI(title="shopyverse-reco-service", version="0.1.0")

app.include_router(routes_reco.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
