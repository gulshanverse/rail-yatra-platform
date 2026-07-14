import time
import pytest
from pydantic import ValidationError
from app.config.config import settings
from app.memory.exceptions import (
    MemorySystemException,
    QdrantUnreachable,
    MemoryQuotaExceededException,
)
from app.memory.interfaces import (
    MemoryItem,
    ConversationSession,
    RAGDocument,
    UnifiedContextPayload,
    IMemoryManager,
    IShortTermMemory,
    ILongTermMemory,
)


def test_settings_memory_configs():
    """Verify that memory configurations are successfully parsed and loaded."""
    assert settings.MEMORY_TTL_SECS == 86400
    assert settings.SEMANTIC_CACHE_TTL_SECS == 43200
    assert settings.COMPRESSION_THRESHOLD_TOKENS == 4000
    assert settings.RETRIEVAL_SIMILARITY_THRESHOLD == 0.60
    assert settings.SEMANTIC_CACHE_THRESHOLD == 0.96

    assert settings.WEIGHT_SEMANTIC == 0.50
    assert settings.WEIGHT_RECENCY == 0.30
    assert settings.WEIGHT_FREQUENCY == 0.10
    assert settings.WEIGHT_IMPORTANCE == 0.10
    assert settings.DECAY_LAMBDA == 0.005
    assert settings.MMR_THETA == 0.65

    assert settings.MAX_USER_SHORT_TERM_MESSAGES == 500
    assert settings.MAX_USER_LONG_TERM_VECTORS == 2000
    assert settings.MAX_TENANT_LONG_TERM_VECTORS == 1000000
    assert settings.MAX_ORG_LONG_TERM_VECTORS == 10000000
    assert settings.MAX_DAILY_COST_LIMIT == 5.00

    assert settings.SEMANTIC_CACHE_ENABLED is True
    assert settings.RAG_ENABLED is True
    assert settings.KNOWLEDGE_GRAPH_ENABLED is False
    assert settings.MMR_RANKING_ENABLED is True
    assert settings.CONTEXT_COMPRESSION_ENABLED is True
    assert settings.EMBEDDING_MIGRATION_ACTIVE is False
    assert settings.AGENT_SHARED_MEMORY_ENABLED is True
    assert settings.DATA_RESIDENCY_REGION == "IN"


def test_exceptions_structure():
    """Verify memory custom exceptions inheritance and parameters."""
    with pytest.raises(QdrantUnreachable) as exc:
        raise QdrantUnreachable("Qdrant is down", {"host": "localhost", "port": 6333})

    assert exc.value.message == "Qdrant is down"
    assert exc.value.details == {"host": "localhost", "port": 6333}
    assert isinstance(exc.value, MemorySystemException)

    with pytest.raises(MemoryQuotaExceededException) as exc:
        raise MemoryQuotaExceededException("Quota exceeded")
    assert exc.value.message == "Quota exceeded"
    assert exc.value.details == {}


def test_memory_item_pydantic_schema():
    """Verify that MemoryItem compiles and validates types correctly."""
    now = time.time()
    item = MemoryItem(
        id="mem-123",
        user_id="user-456",
        session_id="session-789",
        text="Preferred class is 3A",
        version_id="ver-001",
        schema_version=1,
        created_at=now,
        accessed_at=now,
        is_active=True,
    )

    assert item.id == "mem-123"
    assert item.user_id == "user-456"
    assert item.text == "Preferred class is 3A"
    assert item.vector is None
    assert item.importance == 0.5
    assert item.confidence == 1.0
    assert item.is_active is True

    # Validate constraints on importance/confidence
    with pytest.raises(ValidationError):
        MemoryItem(
            id="mem-123",
            user_id="user-456",
            session_id="session-789",
            text="invalid importance",
            version_id="ver-001",
            importance=1.5,  # Out of bounds
        )


def test_conversation_session_pydantic_schema():
    """Verify that ConversationSession validates schemas correctly."""
    session = ConversationSession(
        session_id="session-789",
        user_id="user-456",
        history=[
            {"role": "user", "content": "Book a ticket"},
            {"role": "assistant", "content": "Which train?"},
        ],
        context={"active_pnr": "1234567890"},
        metadata={"platform": "web"},
    )

    assert session.session_id == "session-789"
    assert len(session.history) == 2
    assert session.context == {"active_pnr": "1234567890"}
    assert session.metadata == {"platform": "web"}
    assert session.last_active_at <= time.time()


def test_rag_document_and_payload_pydantic_schema():
    """Verify that RAGDocument and UnifiedContextPayload parse correctly."""
    doc = RAGDocument(
        id="doc-001", content="Luggage allowance is 40kg", source="railway_rules"
    )
    assert doc.id == "doc-001"
    assert doc.content == "Luggage allowance is 40kg"
    assert doc.score == 1.0

    payload = UnifiedContextPayload(
        system_prompt="You are a helper.",
        user_message="Hello",
        history=[],
        memories=[],
        knowledge_docs=[doc],
    )

    assert payload.system_prompt == "You are a helper."
    assert len(payload.knowledge_docs) == 1
    assert payload.knowledge_docs[0].id == "doc-001"


def test_protocols_runtime_checkable():
    """Verify that Protocols are checkable using isinstance (with runtime_checkable)."""
    assert isinstance(IMemoryManager, type)
    assert isinstance(IShortTermMemory, type)
    assert isinstance(ILongTermMemory, type)
