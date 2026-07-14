import json
import logging
import os
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.endpoints import router as api_router
from app.api.intelligence import router as intelligence_router
from app.vector.qdrant import qdrant_rag
from app.data.syncer import railway_background_syncer
from app.memory.short_term import short_term_memory


# JSON Formatter for production logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


# Initialize logger
logger = logging.getLogger("ai-service")
handler = logging.StreamHandler()

if os.getenv("ENV") == "production":
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

app = FastAPI(
    title="RailGPT AI Service",
    description="Microservice responsible for prediction models, recommendation algorithms, and multi-agent systems.",
    version="1.0.0",
)

# Enable CORS
cors_origins_str = os.getenv("CORS_ORIGIN", "*")
cors_origins = cors_origins_str.split(",") if cors_origins_str != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(api_router)
app.include_router(intelligence_router)


@app.on_event("startup")
async def startup_event():
    # 1. Pre-flight Redis connection validation
    redis_healthy = False
    if short_term_memory.redis_client:
        try:
            short_term_memory.redis_client.ping()
            redis_healthy = True
        except Exception as e:
            logger.error(
                f"[FATAL CONNECTION ERROR] Redis ping failed during startup: {e}"
            )

    if os.getenv("ENV") == "production" and not redis_healthy:
        logger.critical(
            "[FATAL CONFIGURATION ERROR] Redis connection is required. Process aborting."
        )
        import sys

        sys.exit(1)

    # 2. Pre-flight Qdrant connection validation (fail-fast in production mode)
    if os.getenv("ENV") == "production" and not qdrant_rag.enabled:
        logger.critical(
            "[FATAL CONNECTION ERROR] Qdrant Cloud connection failed during startup. Process aborting."
        )
        import sys

        sys.exit(1)

    logger.info("Initializing vector search collections in Qdrant...")
    qdrant_rag.initialize_collections()
    logger.info("Starting background synchronization loops...")
    await railway_background_syncer.start()
    logger.info("AI Core Platform started successfully.")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down background synchronization loops...")
    railway_background_syncer.stop()
    if short_term_memory.redis_client:
        try:
            short_term_memory.redis_client.close()
            logger.info("Redis client connection closed gracefully.")
        except Exception as e:
            logger.error(f"Error closing Redis client connection: {e}")
    logger.info("AI Service gracefully shut down.")


@app.get("/health")
def health_check():
    logger.info("Health check endpoint hit")
    qdrant_status = "healthy" if qdrant_rag.enabled else "offline"

    redis_status = "healthy"
    if short_term_memory.redis_client:
        try:
            short_term_memory.redis_client.ping()
        except Exception:
            redis_status = "offline"
    else:
        redis_status = "offline"

    is_all_healthy = qdrant_status == "healthy" and redis_status == "healthy"
    return {
        "status": "healthy" if is_all_healthy else "degraded",
        "service": "ai-service",
        "version": "1.0.0",
        "dependencies": {"qdrant": qdrant_status, "redis": redis_status},
    }


@app.get("/health/ready")
def readiness_check(response: Response):
    redis_up = False
    if short_term_memory.redis_client:
        try:
            short_term_memory.redis_client.ping()
            redis_up = True
        except Exception:
            redis_up = False

    qdrant_up = qdrant_rag.enabled or False

    if redis_up and qdrant_up:
        return {"status": "ready"}
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unready",
            "dependencies": {
                "redis": "healthy" if redis_up else "failed",
                "qdrant": "healthy" if qdrant_up else "failed",
            },
        }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
