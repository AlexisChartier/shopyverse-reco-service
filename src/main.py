# src/main.py

from fastapi import FastAPI
from src.api.routes_reco import router as reco_router
from src.core.database import Base, engine

app = FastAPI(
    title="Shopyverse Recommendation Service",
    version="1.0.0"
)


@app.on_event("startup")
def on_startup():
    """
    Au démarrage de l'application :
    - on crée les tables si elles n'existent pas encore.
    """
    Base.metadata.create_all(bind=engine)


app.include_router(reco_router, prefix="/api", tags=["Recommendations"])


@app.get("/")
def root():
    return {"message": "🚀 Shopyverse Reco Service running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    # Ici tu pourrais tester la DB, mais pour le moment on renvoie "ready"
    return {"status": "ready"}