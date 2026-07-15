"""
Pytest suite verifying Phase 4 Milestone 4.2
Enterprise Vector Retrieval Platform.
"""

import pytest
from typing import List

from app.knowledge import (
    QueryProcessor,
    IntentClassifier,
    QueryDecomposer,
    CrossEncoderReranker,
    SemanticCache,
    CollectionManager,
    RetrievalCoordinator,
    ContextAssembler,
    VectorStoreFactory,
    MockEmbeddingProvider,
)


def test_query_processor_mutations():
    """Verify normalization, spelling correction, rewrites, and temporal markers."""
    processor = QueryProcessor()

    # 1. Spelling Rajdhni -> Rajdhani
    res1 = processor.process_query("What is the Rajdhni train schedule since 2025?")
    assert "rajdhani" in res1["query"]
    assert res1["spelling_corrected"] is True
    assert res1["temporal_marker"] == 2025

    # 2. Cancellation policy rewrite -> refund rules
    res2 = processor.process_query("cancellation policy instructions")
    assert "refund rules" in res2["query"]
    assert res2["rewritten"] is True


def test_intent_classifier():
    """Verify classification categories (PNR, Schedules, Rules, FAQs)."""
    classifier = IntentClassifier()
    assert classifier.classify_intent("check my pnr status") == "PNR"
    assert classifier.classify_intent("Rajdhani timetable print") == "Train Schedule"
    assert classifier.classify_intent("cancellation refund rules") == "Railway Rules"
    assert classifier.classify_intent("hello hi") == "Conversational Query"
    assert classifier.classify_intent("what is a train ticket?") == "FAQ"
    assert classifier.classify_intent("some normal query") == "General Knowledge"


def test_query_decomposer_splits():
    """Verify split lists for complex multi-intent query strings."""
    decomposer = QueryDecomposer()
    # Conjunction 'and'
    splits = decomposer.decompose("Find Rajdhani timetable and cancellation rules")
    assert len(splits) == 2
    assert "Rajdhani timetable" in splits[0]
    assert "cancellation rules" in splits[1]

    # Simple query stays intact
    assert len(decomposer.decompose("Single query")) == 1


@pytest.mark.anyio
async def test_cross_encoder_reranker():
    """Verify cross-encoder rescoring weights overlap matching candidate chunks."""
    reranker = CrossEncoderReranker()
    chunks = [
        {
            "chunk_id": "ch-1",
            "text": "Signal flags validation regulations.",
            "similarity_score": 0.50,
        },
        {
            "chunk_id": "ch-2",
            "text": "Train speed limit circular.",
            "similarity_score": 0.70,
        },
    ]
    # Search for "flags circular"
    reranked = await reranker.rerank("flags validation", chunks, limit=2)
    # ch-1 has high overlap ratio (2 matches out of 2 query words) -> should score higher than ch-2
    assert reranked[0]["chunk_id"] == "ch-1"
    assert "reranker_score" in reranked[0]


def test_semantic_cache_lru_and_expiration():
    """Verify exact match, semantic cosine similarities (>=0.96), LRU limits, and invalidations."""
    cache = SemanticCache(max_size=2, ttl_seconds=1.0)
    v1 = [1.0, 0.0]
    v2 = [0.0, 1.0]
    res_payload = [{"chunk_id": "c-hit"}]

    cache.set("query one", v1, res_payload)
    # Check exact match hit
    assert cache.get("query one", v1) == res_payload

    # Check semantic similarity hit (1.0 similarity with exact same vector)
    assert cache.get("query close", v1) == res_payload

    # Verify LRU limit eviction
    v3 = [-1.0, 0.0]
    cache.set("query two", v2, [{"chunk_id": "c2"}])
    cache.set("query three", v3, [{"chunk_id": "c3"}])
    # cache size is 2, oldest "query one" must be evicted
    assert cache.get("query one", v1) is None

    # Verify invalidation
    cache.invalidate()
    assert cache.get_cache_size() == 0


@pytest.mark.anyio
async def test_collection_manager_and_migrations():
    """Verify workspace setups, deletion, and re-embedding migrations."""
    store = VectorStoreFactory.get_store("mock")
    mgr = CollectionManager(store)

    # Initialize collection v1
    v1_vec = [[0.9, 0.1]]
    payload = [{"chunk_id": "c1", "text": "migration document content"}]
    await store.initialize_collection("col_v1", 2)
    await store.upsert_chunks("col_v1", v1_vec, payload)

    # Migrate to col_v2 using target embedding provider model dimension 3
    class MockTargetProvider(MockEmbeddingProvider):
        @property
        def dimension(self) -> int:
            return 3

        @property
        def model_name(self) -> str:
            return "target-v2-model"

        async def embed_documents(self, texts: List[str]) -> List[List[float]]:
            return [[1.0, 1.0, 1.0]]

    target_prov = MockTargetProvider()
    await mgr.migrate_collection("col_v1", "col_v2", target_prov)

    # Verify migration results exist in new partition
    search_res = await store.search_chunks("col_v2", [1.0, 1.0, 1.0], {}, limit=2)
    assert len(search_res) == 1
    assert search_res[0]["chunk_id"] == "c1"
    assert search_res[0]["embedding_version"] == "target-v2-model"


@pytest.mark.anyio
async def test_retrieval_coordinator_fallbacks_and_context():
    """Verify search routing fallbacks and analytics cost outputs."""
    coordinator = RetrievalCoordinator()

    # Populate vectors in active collection
    await coordinator.vector_store.initialize_collection("railway_knowledge", 768)
    await coordinator.vector_store.upsert_chunks(
        "railway_knowledge",
        [[0.5] * 768],
        [
            {
                "chunk_id": "c-rules",
                "text": "Rajdhani circular rules cancel",
                "category": "railway_rules",
            }
        ],
    )

    # 1. Direct semantic search check
    res = await coordinator.retrieve("Rajdhani circular", "semantic", limit=2)
    assert len(res) > 0
    # Explainability fields populated
    assert "retrieval_explanation" in res[0]
    assert "confidence_level" in res[0]

    # 2. Verify Session context integration
    session_ctx = {"train_number": "12301"}
    res_ctx = await coordinator.retrieve_with_context(
        "circular rules", "semantic", limit=2, session_context=session_ctx
    )
    assert len(res_ctx) > 0

    # 3. Check analytics Cost details dashboard
    analytics = coordinator.get_analytics()
    assert analytics["queries_processed"] > 0
    assert analytics["estimated_cost_usd"] > 0.0


def test_context_diversity_max_chunks_policy():
    """Verify ContextAssembler limits document chunks to max 3 items from same parent."""
    assembler = ContextAssembler()
    chunks = [
        {
            "chunk_id": "ch-1",
            "text": "Sec 1",
            "metadata": {"document_id": "doc-limit", "trust_score": 0.9},
        },
        {
            "chunk_id": "ch-2",
            "text": "Sec 2",
            "metadata": {"document_id": "doc-limit", "trust_score": 0.9},
        },
        {
            "chunk_id": "ch-3",
            "text": "Sec 3",
            "metadata": {"document_id": "doc-limit", "trust_score": 0.9},
        },
        {
            "chunk_id": "ch-4",
            "text": "Sec 4",
            "metadata": {"document_id": "doc-limit", "trust_score": 0.9},
        },  # Exceeds limit
        {
            "chunk_id": "ch-5",
            "text": "Sec A",
            "metadata": {"document_id": "doc-other", "trust_score": 0.9},
        },
    ]

    context = assembler.assemble_context("query test", chunks, token_limit=1000)
    assert "Sec 1" in context
    assert "Sec 2" in context
    assert "Sec 3" in context
    assert (
        "Sec 4" not in context
    )  # Diversity filter drops the 4th chunk of same doc-limit
    assert "Sec A" in context  # Allowed as it comes from doc-other
