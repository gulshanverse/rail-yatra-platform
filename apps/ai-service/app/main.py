import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.endpoints import router as api_router
from app.api.intelligence import router as intelligence_router
from app.vector.qdrant import qdrant_rag

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ai-service")

app = FastAPI(
    title="RailGPT AI Service",
    description="Microservice responsible for prediction models, recommendation algorithms, and multi-agent systems.",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(api_router)
app.include_router(intelligence_router)


@app.on_event("startup")
def startup_event():
    logger.info("Initializing vector search collections in Qdrant...")
    qdrant_rag.initialize_collections()
    logger.info("AI Core Platform started successfully.")

@app.get("/health")
def health_check():
    logger.info("Health check endpoint hit")
    return {
        "status": "healthy",
        "service": "ai-service",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

