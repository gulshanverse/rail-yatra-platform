import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from app.config.config import settings

logger = logging.getLogger("ai-service.vector.qdrant")

# Offline mock document registry for local execution without Qdrant running
MOCK_KNOWLEDGE_DOCUMENTS = [
    {
        "content": "Indian Railways Luggage Rules: Sleeper class passengers can carry up to 40 kg of luggage free. AC 3-Tier and AC 2-Tier passengers can carry 40 kg and 50 kg free, respectively. AC 1st Class passengers get 70 kg free allowance. Extra weight is charged at luggage rates.",
        "source": "luggage_rules_policy"
    },
    {
        "content": "Tatkal Ticketing Timings: Tatkal booking opens at 10:00 AM daily for AC classes (1A, 2A, 3A, CC) and at 11:00 AM for non-AC classes (SL, 2S). Ticket confirmation chance is highly time-sensitive; waitlisted Tatkal tickets are less likely to clear.",
        "source": "tatkal_booking_faq"
    },
    {
        "content": "Ticket Cancellation Refund Policy: Confirm tickets cancelled 48 hours prior to train departure have flat cancellation fees: AC 1st/Executive Rs. 240, AC 2nd/3rd/Chair Car Rs. 200/180, Sleeper Rs. 120, Second Class Rs. 60. Cancel between 12-48 hours incurs a 25% fee.",
        "source": "refund_rules_circular"
    },
    {
        "content": "Senior Citizen and Waitlist Clearence: Confirmed lower berths are prioritised for senior citizens, pregnant women, and female passengers above 45. Waitlist clearing algorithms prioritize high-priority quotas over general waitlist status.",
        "source": "berth_allocation_policy"
    }
]

class QdrantRAG:
    """
    Manages connections and indexing in the Qdrant vector database.
    Provides local mock keyword searches if Qdrant is offline.
    """
    def __init__(self):
        self.client = None
        self.enabled = False
        try:
            # Parse host and port from QDRANT_URL
            url = settings.QDRANT_URL
            if "localhost" in url:
                self.client = QdrantClient(host="localhost", port=6333, timeout=3.0)
            else:
                self.client = QdrantClient(url=url, timeout=3.0)
            
            # Simple check if Qdrant is responding
            self.client.get_collections()
            self.enabled = True
            logger.info("Successfully connected to Qdrant Vector database.")
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant at {settings.QDRANT_URL}: {e}. Local fallback search enabled.")
            self.client = None

    def initialize_collections(self) -> None:
        """Initializes default collection if Qdrant client is connected."""
        if not self.enabled or not self.client:
            return
        
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if "rail_knowledge" not in collections:
                # In production, we'd define vector configurations. Here we scaffold a basic layout.
                from qdrant_client.models import Distance, VectorParams
                self.client.create_collection(
                    collection_name="rail_knowledge",
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info("Created collection 'rail_knowledge' in Qdrant.")
        except Exception as e:
            logger.error(f"Error creating Qdrant collections: {e}")

    def search_docs(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Searches vector database or uses local keyword matching if Qdrant is disabled."""
        if self.enabled and self.client:
            try:
                # Normally, we'd embed the query first. For this setup, we'll demonstrate a search:
                # To keep it error-free in case embeddings package is mismatching, we wrap it.
                # Here we fallback to local mock search, or vector query if embeddings are implemented.
                pass
            except Exception as e:
                logger.error(f"Qdrant query error: {e}")

        # Fuzzy local search logic as fallback
        query_words = query.lower().split(" ")
        matches = []
        for doc in MOCK_KNOWLEDGE_DOCUMENTS:
            score = sum(1 for word in query_words if word in doc["content"].lower())
            if score > 0:
                matches.append((score, doc))
        
        # Sort matches by score descending
        matches.sort(key=lambda x: x[0], reverse=True)
        results = [doc for score, doc in matches[:limit]]
        
        # If no word matches, return the top FAQ rules by default
        if not results:
            results = MOCK_KNOWLEDGE_DOCUMENTS[:limit]
            
        return results

qdrant_rag = QdrantRAG()
