import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

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

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None

@app.get("/health")
def health_check():
    logger.info("Health check endpoint hit")
    return {
        "status": "healthy",
        "service": "ai-service",
        "version": "1.0.0"
    }

@app.post("/chat")
def basic_chat(request: ChatRequest):
    logger.info(f"Received query: {request.message} for conversation: {request.conversation_id}")
    return {
        "reply": f"AI-First core parser received query: '{request.message}'",
        "parsed_intent": "search_train",
        "confidence": 0.95
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
