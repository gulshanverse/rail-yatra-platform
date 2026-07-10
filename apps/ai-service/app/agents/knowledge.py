import logging
from app.agents.base import BaseAgent

logger = logging.getLogger("ai-service.agents.knowledge")

KNOWLEDGE_PROMPT = """You are the Knowledge Retrieval Agent. Your job is to fetch guidelines and policy terms from the Qdrant vector database.

When responding:
1. Ground your answers strictly on the retrieved knowledge documents.
2. Cite the source or policy circular if available.
3. If the information is not in the knowledge base, state clearly that you do not know, rather than fabricating.
"""

class KnowledgeAgent(BaseAgent):
    """
    Agent responsible for interfacing with vector DB context for RAG inquiries.
    """
    def __init__(self):
        super().__init__(
            name="KnowledgeAgent",
            system_prompt=KNOWLEDGE_PROMPT
        )
