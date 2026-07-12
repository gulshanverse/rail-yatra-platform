"""
Interface definitions, type contracts, Pydantic schemas, and protocols
for the RailYatra AI Memory Layer & Context Engine.
"""

from typing import Dict, Any, List, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, Field
import time

# =====================================================================
# Pydantic Schemas / Core Models
# =====================================================================

class MemoryItem(BaseModel):
    """
    Represents an individual memory fact or user preference stored in 
    the long-term vector database.
    """
    id: str = Field(description="Unique memory item UUID")
    user_id: str = Field(description="Unique owner traveler ID")
    session_id: str = Field(description="Session ID where the memory originated")
    text: str = Field(description="Sanitized text content of the memory")
    vector: Optional[List[float]] = Field(default=None, description="Optional dense embedding vector")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")
    version_id: str = Field(description="UUID representing this version state")
    parent_version_id: Optional[str] = Field(default=None, description="Parent version state UUID")
    schema_version: int = Field(default=1, description="Data schema version for evolutionary mapping")
    created_at: float = Field(default_factory=time.time, description="Creation timestamp")
    accessed_at: float = Field(default_factory=time.time, description="Last access timestamp")
    access_count: int = Field(default=0, description="Read counter for frequency analytics")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score (0.0 to 1.0)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Cognitive confidence score (0.0 to 1.0)")
    is_active: bool = Field(default=True, description="Soft deletion/active state toggle")

class ConversationSession(BaseModel):
    """
    Represents short-term session state, including message loops and
    transient contexts.
    """
    session_id: str
    user_id: str
    history: List[Dict[str, Any]] = Field(default_factory=list, description="Sliding window chat history messages")
    context: Dict[str, Any] = Field(default_factory=dict, description="Transient session parameters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="System metadata parameters")
    last_active_at: float = Field(default_factory=time.time)

class RAGDocument(BaseModel):
    """
    Represents a retrieved static/dynamic railway rules policy, schedule,
    or guidelines snippet.
    """
    id: str
    content: str
    source: str
    score: float = Field(default=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class UnifiedContextPayload(BaseModel):
    """
    Final prompt input representation hydrated by the Context Engine
    prior to model forward execution.
    """
    system_prompt: str
    user_message: str
    history: List[Dict[str, Any]]
    memories: List[MemoryItem]
    knowledge_docs: List[RAGDocument]
    metadata: Dict[str, Any] = Field(default_factory=dict)

# =====================================================================
# Protocols / Component Interfaces
# =====================================================================

@runtime_checkable
class IEmbeddingProvider(Protocol):
    """Abstraction for generating dense vectors from text inputs."""
    async def embed_query(self, text: str) -> List[float]:
        """Generates embedding for a single search string."""
        ...

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of document strings."""
        ...

@runtime_checkable
class IShortTermMemory(Protocol):
    """Interface for sub-millisecond conversation tracking (Redis)."""
    async def save_session_context(self, session_id: str, context_data: Dict[str, Any], expire_seconds: int = 86400) -> None:
        """Caches session context variables."""
        ...

    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Retrieves cached session context variables."""
        ...

    async def add_message(self, session_id: str, role: str, content: str, limit: int = 20) -> None:
        """Appends message to the active sliding window history."""
        ...

    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieves list of messages in the sliding history window."""
        ...

    async def clear_session(self, session_id: str) -> None:
        """Deletes session context and history keys."""
        ...

@runtime_checkable
class ILongTermMemory(Protocol):
    """Interface for semantic persistence (Qdrant)."""
    async def save_memory(self, memory: MemoryItem) -> None:
        """Saves or updates a versioned semantic memory item."""
        ...

    async def retrieve_memories(self, user_id: str, query_vector: List[float], limit: int = 5, tenant_id: Optional[str] = None) -> List[MemoryItem]:
        """Queries vectors by proximity, filtering by user and tenant boundaries."""
        ...

    async def delete_memory(self, user_id: str, memory_id: str) -> None:
        """Performs soft delete on a specific memory node."""
        ...

    async def clear_user_memories(self, user_id: str) -> None:
        """Permanently purges all vectors matching a user identifier."""
        ...

    async def get_versions(self, memory_id: str) -> List[MemoryItem]:
        """Retrieves the history tree for a specific memory item."""
        ...

@runtime_checkable
class IMemoryRanker(Protocol):
    """Sorts retrieved items using decayed relevance scoring and MMR."""
    def score_memories(self, items: List[MemoryItem], query: str, config: Dict[str, Any]) -> List[MemoryItem]:
        """Calculates unified rank score combining similarity, recency, and frequency."""
        ...

    def apply_mmr(self, items: List[MemoryItem], query_vector: List[float], limit: int = 5, theta: float = 0.65) -> List[MemoryItem]:
        """Reduces redundancy by applying Maximal Marginal Relevance filter."""
        ...

@runtime_checkable
class ICognitiveStage(Protocol):
    """Individual preprocessing node in the extraction pipeline."""
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mutates execution payload state, passing outputs to next block."""
        ...

@runtime_checkable
class IEventDispatcher(Protocol):
    """Event Bus mechanism enabling decoupled pub/sub tasks."""
    async def dispatch(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Broadcasts event type and context details to listeners."""
        ...

    def register_listener(self, event_type: str, listener: Any) -> None:
        """Registers a callback method for a specific event key."""
        ...

@runtime_checkable
class IEntityGraph(Protocol):
    """Provider-independent interface for tracking node relations."""
    async def create_node(self, label: str, properties: Dict[str, Any]) -> str:
        """Inserts a node into the graph space."""
        ...

    async def create_relationship(self, source_id: str, target_id: str, rel_type: str, properties: Dict[str, Any]) -> None:
        """Links two nodes together with a typed edge relationship."""
        ...

    async def query_relationships(self, node_id: str) -> List[Dict[str, Any]]:
        """Queries edges connected to a target node."""
        ...

@runtime_checkable
class IArchiveStorage(Protocol):
    """Provider-independent interface for cold archive storage."""
    async def archive(self, key: str, payload: Dict[str, Any]) -> None:
        """Saves compressed data payload to cold storage buckets."""
        ...

    async def restore(self, key: str) -> Dict[str, Any]:
        """Retrieves and decompresses historical payload."""
        ...

@runtime_checkable
class IMemoryManager(Protocol):
    """Public facade orchestrating active short-term and long-term actions."""
    async def save_interaction(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None
    ) -> bool:
        """Scrubs PII, updates sliding cache, and dispatches long-term vector tasks."""
        ...

    async def retrieve(self, user_id: str, session_id: str, query: str, limit: int = 5, tenant_id: Optional[str] = None) -> List[MemoryItem]:
        """Retrieves sorted, security-isolated semantic items matching query context."""
        ...

    async def search(self, user_id: str, query: str, limit: int = 10, tenant_id: Optional[str] = None) -> List[MemoryItem]:
        """Performs raw similarity lookup in Qdrant."""
        ...

    async def delete(self, user_id: str, memory_id: str) -> None:
        """Soft deletes memory point."""
        ...

    async def clear(self, user_id: str, session_id: str) -> None:
        """Clears short-term active caches and marks matching vectors inactive."""
        ...

    async def pin(self, user_id: str, memory_id: str) -> None:
        """Sets a permanent flag to prevent temperature decay on a record."""
        ...

    async def forget(self, user_id: str) -> None:
        """Permanently purges all active/inactive vectors for GDPR compliance."""
        ...

    async def rollback(self, user_id: str, memory_id: str, target_version_id: str) -> None:
        """Reverts active pointer state to previous version tree node."""
        ...

    def compare_versions(self, version_a: MemoryItem, version_b: MemoryItem) -> Dict[str, Any]:
        """Returns JSON comparison showing text delta differences."""
        ...

@runtime_checkable
class IContextEngine(Protocol):
    """Context compiler and prompt template hydrator."""
    async def assemble_context(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        system_instructions: str,
        limit_tokens: int = 4000,
        tenant_id: Optional[str] = None
    ) -> UnifiedContextPayload:
        """Builds security-validated prompts mapping token budget constraints."""
        ...
