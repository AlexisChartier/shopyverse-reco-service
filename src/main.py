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
