from fastapi import FastAPI
from src.api.routes_reco import router as reco_router

app = FastAPI(
    title="Shopyverse Recommendation Service",
    version="1.0.0"
)

app.include_router(reco_router, prefix="/api", tags=["Recommendations"])

@app.get("/")
def root():
    return {"message": "🚀 Shopyverse Reco Service running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/ready")
async def ready():
    # check DB connectivity or model ready flag
    try:
        # ex: faire une courte requête simple
        # engine is your SQLAlchemy engine
        # with engine.connect() as conn:
        #     conn.execute("SELECT 1")
        pass
    except Exception:
        return {"status": "unready"}, 503
    return {"status": "ready"}