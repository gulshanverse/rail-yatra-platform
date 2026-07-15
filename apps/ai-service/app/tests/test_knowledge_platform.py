"""
Pytest suite verifying Phase 4 Milestone 4.1
Enterprise Knowledge & Embedding Platform.
"""

import pytest
from typing import Dict, Any
from unittest.mock import patch

from app.knowledge import (
    IKnowledgeSource,
    KnowledgeSourceRegistry,
    ProcessingPipeline,
    ChunkingEngine,
    FixedSizeChunkingStrategy,
    HeadingAwareChunkingStrategy,
    SemanticSentenceChunkingStrategy,
    HierarchicalChunkingStrategy,
    EmbeddingFactory,
    VectorStoreFactory,
    IndexManager,
    RetrievalCoordinator,
    ContextAssembler,
    DocumentIngestionPipeline,
    VersionManager,
    DatasetVersionManager,
    IngestionException,
    ProcessingException,
)


# Mock source implementation for validation testing
class MockKnowledgeSource(IKnowledgeSource):
    def __init__(self, source_id: str, content_data: str) -> None:
        self._id = source_id
        self._content = content_data

    @property
    def source_id(self) -> str:
        return self._id

    @property
    def metadata(self) -> Dict[str, Any]:
        return {"category": "test_docs", "authority_level": "railway_board"}

    async def fetch_payload(self) -> bytes:
        return self._content.encode("utf-8")


@pytest.mark.anyio
async def test_knowledge_source_registry():
    """Verify registry loads, lists, and returns registered sources."""
    registry = KnowledgeSourceRegistry()
    source = MockKnowledgeSource("src-1", "circular data")

    registry.register_source(source)
    assert "src-1" in registry.list_sources()

    loaded = registry.get_source("src-1")
    assert loaded.source_id == "src-1"

    registry.deregister_source("src-1")
    assert "src-1" not in registry.list_sources()


def test_processing_pipeline_mutations():
    """Verify cleaner, redactor, language tagger, and scorer pipeline step changes."""
    pipeline = ProcessingPipeline()
    raw_payload = "Railway circular: passenger phone number is 9876543210. Clear spacing.  ".encode(
        "utf-8"
    )
    meta = {
        "document_id": "doc-1",
        "category": "circulars",
        "tags": ["fares"],
        "authority_level": "railway_board",
    }

    content, updated_meta = pipeline.execute(raw_payload, meta)
    text = content.decode("utf-8")

    # 1. PII Redacted
    assert "[REDACTED_PHONE]" in text or "[REDACTED_PNR]" in text
    # 2. Spacing Normalized
    assert "spacing." in text
    # 3. Language detected
    assert updated_meta["language"] == "en"
    # 4. Composite Trust Score computed (Board has high weight)
    assert updated_meta["trust_score"] > 0.8


def test_chunking_strategies_splits():
    """Verify fixed, header-aware, sentence-aware, and hierarchical splits."""
    doc_meta = {"document_id": "doc-split"}
    text = "# Section One\nSentence one. Sentence two. Sentence three.\n# Section Two\nSentence four."

    # 1. Fixed Size Splitter
    engine = ChunkingEngine(FixedSizeChunkingStrategy(chunk_size=5, overlap=1))
    chunks = engine.execute_chunking(text, doc_meta)
    assert len(chunks) > 0
    assert chunks[0]["metadata"]["chunking_strategy"] == "fixed_size"

    # 2. Heading Aware Splitter
    engine.set_strategy(HeadingAwareChunkingStrategy())
    chunks = engine.execute_chunking(text, doc_meta)
    assert len(chunks) == 2
    assert chunks[0]["metadata"]["chunk_header"] == "Section One"

    # 3. Semantic Sentence Splitter
    engine.set_strategy(SemanticSentenceChunkingStrategy())
    # Modify settings mock target limit to check splits
    chunks = engine.execute_chunking(text, doc_meta)
    assert len(chunks) > 0

    # 4. Hierarchical splitter (parent -> child links)
    engine.set_strategy(HierarchicalChunkingStrategy(parent_size=10, child_size=3))
    chunks = engine.execute_chunking(text, doc_meta)
    assert len(chunks) > 0
    # Child points to parent link
    child_chunks = [
        c for c in chunks if c["metadata"]["chunking_strategy"] == "hierarchical_child"
    ]
    if child_chunks:
        assert child_chunks[0]["metadata"]["relationships"][0]["type"] == "child_of"


@pytest.mark.anyio
async def test_embedding_factory_and_evaluation():
    """Verify mock vector dimensions and performance evaluator output."""
    provider = EmbeddingFactory.get_provider("mock")
    assert provider.model_name == "mock-embedding-model"

    vector = await provider.embed_query("train seat search")
    assert len(vector) == provider.dimension

    from app.knowledge.embedding import EmbeddingEvaluator

    ev = EmbeddingEvaluator()
    perf = ev.evaluate_performance(provider, [{"query": "q", "doc": "d"}])
    assert "precision" in perf
    assert perf["average_latency_ms"] == 15.4


@pytest.mark.anyio
async def test_vector_store_cosine_similarity_search():
    """Verify indexing upserts, cosine similarity queries, and segment deletes."""
    store = VectorStoreFactory.get_store("mock")
    await store.initialize_collection("test_col", 3)

    # Index two vectors
    # v1 is closer to query_vec [1, 0, 0] than v2
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    query_vec = [0.9, 0.1, 0.0]

    payloads = [
        {"chunk_id": "c-1", "parent_document": "d-a", "category": "trains"},
        {"chunk_id": "c-2", "parent_document": "d-a", "category": "stations"},
    ]

    await store.upsert_chunks("test_col", [v1, v2], payloads)

    # Search under category "trains"
    matches = await store.search_chunks(
        "test_col",
        query_vector=query_vec,
        filter_metadata={"category": "trains"},
        limit=2,
    )
    assert len(matches) == 1
    assert matches[0]["chunk_id"] == "c-1"
    assert matches[0]["similarity_score"] > 0.8

    # Index manager segment deletes
    mgr = IndexManager(store)
    mgr.active_collection = "test_col"
    await mgr.remove_document_chunks("d-a")

    matches_after = await store.search_chunks(
        "test_col", query_vector=query_vec, filter_metadata={}, limit=2
    )
    assert len(matches_after) == 0


@pytest.mark.anyio
async def test_retrieval_policy_routing():
    """Verify retrieval coordinator query execution routing under policies."""
    coordinator = RetrievalCoordinator()
    # Mock index manager to populate vectors in the default collection
    v1 = [0.9] * 768
    payload = {"chunk_id": "chunk-r1", "parent_document": "doc-r1", "category": "rules"}

    await coordinator.vector_store.initialize_collection("railway_knowledge", 768)
    await coordinator.vector_store.upsert_chunks("railway_knowledge", [v1], [payload])

    # Retrieve with policy
    res = await coordinator.retrieve("safety circulars", "rules", limit=1)
    assert len(res) == 1
    assert res[0]["chunk_id"] == "chunk-r1"


def test_context_assembler_budget_packing():
    """Verify prompt formatting, deduplication, and budget truncation checks."""
    assembler = ContextAssembler()
    chunks = [
        {
            "chunk_id": "ch-1",
            "text": "Sentence A.",
            "metadata": {"document_id": "doc-a", "trust_score": 0.9},
        },
        {
            "chunk_id": "ch-2",
            "text": "Sentence A.",
            "metadata": {"document_id": "doc-a", "trust_score": 0.9},
        },  # Duplicate
        {
            "chunk_id": "ch-3",
            "text": "Sentence B.",
            "metadata": {"document_id": "doc-b", "trust_score": 0.7},
        },
    ]

    # Limit tokens to force fit
    context = assembler.assemble_context("query test", chunks, token_limit=25)
    assert "Sentence A" in context
    # Duplicate block is skipped
    assert context.count("Sentence A") == 1


@pytest.mark.anyio
async def test_document_ingestion_transaction_flow():
    """Verify end-to-end ingestion pipeline, registration catalog, and failure rollbacks."""
    pipeline = DocumentIngestionPipeline()
    raw_payload = (
        "Railway Operating Rule 101. Signal flags must be validated hourly.".encode(
            "utf-8"
        )
    )
    meta = {
        "document_id": "doc-ingest",
        "category": "operating_rules",
        "tags": ["signals"],
        "authority_level": "railway_board",
    }

    # Ingest document
    status = await pipeline.ingest("doc-ingest", raw_payload, "source-board", meta)
    assert status == "PUBLISHED"

    # Document registered in registry catalog
    doc_record = pipeline.registry.get_document("doc-ingest")
    assert doc_record is not None
    assert doc_record["status"] == "PUBLISHED"

    # Verify rollback triggers during indexing errors
    # Mock index_batch to raise database error
    with patch.object(
        pipeline.index_mgr, "index_batch", side_effect=Exception("Database down")
    ):
        with pytest.raises(IngestionException):
            await pipeline.ingest("doc-fail", raw_payload, "source-board", meta)

        # Ensure document registry entry does not exist (rolled back)
        assert pipeline.registry.get_document("doc-fail") is None


def test_version_managers():
    """Verify schema, embedding compatibility matrices, and dataset state rolls."""
    vm = VersionManager(
        index_version="v1",
        schema_version="s1",
        embedding_version="e1",
        chunk_version="c1",
    )
    other_ok = {
        "index_version": "v1",
        "schema_version": "s1",
        "embedding_version": "e1",
        "chunk_version": "c1",
    }
    other_fail = {
        "index_version": "v2",
        "schema_version": "s1",
        "embedding_version": "e1",
        "chunk_version": "c1",
    }

    assert vm.validate_compatibility(other_ok) is True
    assert vm.validate_compatibility(other_fail) is False

    # Dataset manager transitions
    dm = DatasetVersionManager(initial_version="dataset_v1")
    dm.trigger_migration("dataset_v2")
    assert dm.current_version == "dataset_v2"

    dm.trigger_rollback()
    assert dm.current_version == "dataset_v1"

    # Quality scoring boundary conditions
    from app.knowledge.processing import QualityScorerProcessor

    scorer = QualityScorerProcessor()
    _, score_meta = scorer.process(b"data", {"authority_level": "unknown"})
    assert score_meta["trust_score"] < 0.6

    # Cleaner exceptions testing
    from app.knowledge.processing import TextCleanerProcessor

    cleaner = TextCleanerProcessor()
    with pytest.raises(ProcessingException):
        cleaner.process(b"\x80invalid_bytes", {})
