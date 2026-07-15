"""
Retrieval Platform: Routing Policy engine, Query Processing, Intent Classification,
Decomposition, Cross-Encoder Re-ranking, and Retrieval Coordinator with fallbacks.
"""

import time
import logging
from typing import Dict, Any, List, Tuple, Optional

from app.knowledge.interfaces import (
    IRetrievalPolicy,
    IRetrievalCoordinator,
    IEmbeddingProvider,
    IVectorStore,
    IIntentClassifier,
    IQueryDecomposer,
    ICrossEncoderReranker,
)
from app.knowledge.exceptions import RetrievalException
from app.knowledge.embedding import EmbeddingFactory
from app.knowledge.vector_store import VectorStoreFactory
from app.knowledge.cache import SemanticCache

logger = logging.getLogger("ai-service.knowledge.retrieval")


class QueryProcessor:
    """Normalizes, cleans, spelling corrects, and rewrites queries."""

    def process_query(self, query: str) -> Dict[str, Any]:
        normalized = query.lower().strip()

        # Mock spelling correction
        corrected = normalized
        if "rajdhni" in normalized:
            corrected = corrected.replace("rajdhni", "rajdhani")
        if "schdule" in normalized:
            corrected = corrected.replace("schdule", "schedule")

        # Mock query rewriting
        rewritten = corrected
        if "cancellation policy" in corrected:
            rewritten = rewritten.replace("cancellation policy", "refund rules")

        # Temporal marker detection
        temporal_marker = None
        for year in ["2024", "2025", "2026"]:
            if year in normalized:
                temporal_marker = int(year)
                break

        return {
            "query": rewritten,
            "original_query": query,
            "spelling_corrected": corrected != normalized,
            "rewritten": rewritten != normalized,
            "temporal_marker": temporal_marker,
        }


class IntentClassifier(IIntentClassifier):
    """Categorizes traveler query intent categories."""

    def classify_intent(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["pnr", "ticket status", "booking status"]):
            return "PNR"
        if any(
            w in q
            for w in ["schedule", "timetable", "train time", "arrival", "departure"]
        ):
            return "Train Schedule"
        if any(w in q for w in ["rule", "policy", "refund", "cancel", "circular"]):
            return "Railway Rules"
        if any(w in q for w in ["hi", "hello", "how are you", "who are you"]):
            return "Conversational Query"
        if "?" in q or any(w in q for w in ["what", "how", "why", "where", "who"]):
            return "FAQ"
        return "General Knowledge"


class QueryDecomposer(IQueryDecomposer):
    """Decomposes complex multi-topic queries into lists of sub-queries."""

    def decompose(self, query: str) -> List[str]:
        q = query.strip()
        conjunctions = [" and ", " as well as ", "; "]
        for conj in conjunctions:
            if conj in q:
                parts = [p.strip() for p in q.split(conj) if p.strip()]
                return parts
        return [q]


class CrossEncoderReranker(ICrossEncoderReranker):
    """Vendor-independent semantic cross-encoder re-ranking stage."""

    async def rerank(
        self, query: str, chunks: List[Dict[str, Any]], limit: int
    ) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        scored_chunks = []
        query_words = set(query.lower().split())

        for chunk in chunks:
            text = chunk.get("text", "").lower()
            # Overlay simple term overlap score as mock cross-encoder scoring
            match_count = sum(1 for w in query_words if w in text)
            overlap_ratio = match_count / max(1, len(query_words))

            orig_score = chunk.get("similarity_score", 0.70)
            # Rerank score is a blend of semantic distance and exact term matches
            rerank_score = (0.4 * orig_score) + (0.6 * overlap_ratio)

            chunk_copy = dict(chunk)
            chunk_copy["reranker_score"] = float(rerank_score)
            chunk_copy["similarity_score"] = float(
                rerank_score
            )  # Hot-swap similarity rank
            scored_chunks.append(chunk_copy)

        # Re-sort descending
        scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_chunks[:limit]


class RetrievalPolicy(IRetrievalPolicy):
    """Filters queries and configures search arguments according to policy definitions."""

    def apply_policy(
        self, query: str, config: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        policy_type = config.get("policy_type", "hybrid").lower()
        metadata_filters = {}

        if "category" in config:
            metadata_filters["category"] = config["category"]

        if "last_updated_after" in config:
            metadata_filters["updated_at"] = config["last_updated_after"]

        if "security_classification" in config:
            metadata_filters["security_classification"] = config[
                "security_classification"
            ]

        return policy_type, metadata_filters


class RetrievalCoordinator(IRetrievalCoordinator):
    """Orchestrates intent routing, caches, fusion searches, and fallback stages."""

    def __init__(
        self,
        embedding_provider: IEmbeddingProvider = None,
        vector_store: IVectorStore = None,
    ) -> None:
        self.embedding_provider = embedding_provider or EmbeddingFactory.get_provider()
        self.vector_store = vector_store or VectorStoreFactory.get_store()

        self.query_processor = QueryProcessor()
        self.intent_classifier = IntentClassifier()
        self.query_decomposer = QueryDecomposer()
        self.reranker = CrossEncoderReranker()
        self.policy_engine = RetrievalPolicy()
        self.cache = SemanticCache()

        self.active_collection = "railway_knowledge"

        # Observability Cost & Analytics metrics
        self.analytics = {
            "queries_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "cache_savings_usd": 0.0,
            "fallback_events": 0,
            "policy_distribution": {},
            "zero_result_queries": 0,
        }

    def get_analytics(self) -> Dict[str, Any]:
        """Exposes dashboard statistics for observability ingestion."""
        return dict(self.analytics)

    async def retrieve(
        self, query: str, policy_name: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        # Inretrieve supporting optional parameters wrapper
        return await self.retrieve_with_context(query, policy_name, limit)

    async def retrieve_with_context(
        self,
        query: str,
        policy_name: str,
        limit: int = 10,
        session_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        start_time = time.time()
        self.analytics["queries_processed"] += 1

        try:
            # 1. Process query
            proc_res = self.query_processor.process_query(query)
            clean_query = proc_res["query"]

            # 2. Inquire intent classifier
            intent = self.intent_classifier.classify_intent(clean_query)
            self.analytics["policy_distribution"][intent] = (
                self.analytics["policy_distribution"].get(intent, 0) + 1
            )

            # 3. Handle query decomposition for multi-topic questions
            sub_queries = self.query_decomposer.decompose(clean_query)

            # 4. Integrate session context keywords if present
            context_query = clean_query
            if session_context and "train_number" in session_context:
                context_query = f"{session_context['train_number']} {clean_query}"
                logger.info(f"Context enriched query: '{context_query}'")

            # 5. Generate embedding representation (costed lookup)
            emb_start = time.time()
            query_vector = await self.embedding_provider.embed_query(context_query)
            emb_latency = time.time() - emb_start

            # Cost model accounting: embed token calculations
            approx_tokens = len(context_query.split()) * 2
            self.analytics["total_tokens"] += approx_tokens
            # $0.0001 per 1k input tokens estimation
            cost_estimation = (approx_tokens / 1000.0) * 0.0001

            # 6. Check Semantic Cache
            cache_start = time.time()
            cached_hits = self.cache.get(context_query, query_vector)
            cache_latency = time.time() - cache_start

            if cached_hits is not None:
                self.analytics["cache_hits"] += 1
                self.analytics["cache_savings_usd"] += cost_estimation
                logger.info("Retrieval context resolved from cache successfully.")
                return cached_hits

            self.analytics["cache_misses"] += 1
            self.analytics["estimated_cost_usd"] += cost_estimation

            # 7. Execute Retrieval Fallback Sequence
            policy_config = {"policy_type": policy_name}
            policy_type, filters = self.policy_engine.apply_policy(
                context_query, policy_config
            )

            results = []
            applied_policy = policy_type
            if applied_policy not in ["semantic", "hybrid", "keyword", "faq"]:
                applied_policy = "semantic"

            # Fallback Stage 1: Semantic search
            if applied_policy == "semantic":
                results = await self.vector_store.search_chunks(
                    self.active_collection, query_vector, filters, limit
                )
                # If low confidence match, trigger fallback to Hybrid
                if (
                    results
                    and max(r.get("similarity_score", 0) for r in results) < 0.65
                ):
                    logger.warning(
                        "Low semantic confidence. Falling back to Hybrid search."
                    )
                    applied_policy = "hybrid"
                    self.analytics["fallback_events"] += 1

            # Fallback Stage 2: Hybrid search (Vector + Lexical RRF)
            if applied_policy == "hybrid":
                results = await self._execute_hybrid_rrf(
                    query_vector, context_query, filters, limit
                )
                if not results:
                    logger.warning(
                        "Hybrid search returned empty. Falling back to Keyword search."
                    )
                    applied_policy = "keyword"
                    self.analytics["fallback_events"] += 1

            # Fallback Stage 3: Keyword search
            if applied_policy == "keyword":
                results = await self._execute_lexical_search(
                    context_query, filters, limit
                )
                if not results:
                    logger.warning(
                        "Keyword search returned empty. Falling back to FAQ search."
                    )
                    applied_policy = "faq"
                    self.analytics["fallback_events"] += 1

            # Fallback Stage 4: FAQ search
            if applied_policy == "faq":
                results = await self.vector_store.search_chunks(
                    "faq_knowledge", query_vector, filters, limit
                )

            # Fallback Stage 5: No result final catch
            if not results:
                logger.warning(
                    f"No results found for query '{query}' after executing fallback chain."
                )
                self.analytics["zero_result_queries"] += 1
                return []

            # 8. Cross-Encoder Re-ranking
            rerank_start = time.time()
            reranked_results = await self.reranker.rerank(context_query, results, limit)
            rerank_latency = time.time() - rerank_start

            # 9. Apply Confidence Scoring & Explainability logs to payloads
            final_results = []
            for item in reranked_results:
                score = item.get("similarity_score", 0.0)

                # Confidence Levels
                if score >= 0.85:
                    confidence = "HIGH"
                elif score >= 0.65:
                    confidence = "MEDIUM"
                else:
                    confidence = "LOW"

                # Explainability Metadata
                explanation = {
                    "selected_policy": applied_policy,
                    "ranking_contribution": {
                        "original_similarity": float(score),
                        "rerank_score": float(item.get("reranker_score", score)),
                    },
                    "applied_filters": {"collection": self.active_collection},
                    "retrieval_reason": f"Matched intent category: {intent} via {applied_policy} search.",
                }

                item_copy = dict(item)
                item_copy["confidence_level"] = confidence
                item_copy["retrieval_explanation"] = explanation
                final_results.append(item_copy)

            # 10. Cache results for subsequent query runs
            self.cache.set(context_query, query_vector, final_results)

            total_latency = time.time() - start_time
            logger.info(
                f"Retrieval pipeline complete. Output {len(final_results)} chunks. "
                f"Latencies: embed={emb_latency:.4f}s, cache={cache_latency:.4f}s, "
                f"rerank={rerank_latency:.4f}s, total={total_latency:.4f}s. "
                f"Decomposed sub-queries count: {len(sub_queries)}"
            )
            return final_results

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            raise RetrievalException(f"Retrieval coordinator operation failed: {e}")

    async def _execute_lexical_search(
        self, query: str, filters: Dict[str, Any], limit: int
    ) -> List[Dict[str, Any]]:
        """Simulates BM25 style keyword substring overlap search on collection chunks."""
        query_words = [w.lower() for w in query.split() if len(w) > 2]
        if not query_words:
            return []

        # Safely extract from active mock store collection list
        if not hasattr(self.vector_store, "_collections"):
            return []

        candidates = []
        with self.vector_store._lock:
            col_list = self.vector_store._collections.get(self.active_collection, [])
            for _, payload in col_list:
                text = payload.get("text", "").lower()
                matches = sum(1 for w in query_words if w in text)
                if matches > 0:
                    score = matches / len(query_words)
                    payload_copy = dict(payload)
                    payload_copy["similarity_score"] = float(score)
                    candidates.append(payload_copy)

        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        return candidates[:limit]

    async def _execute_hybrid_rrf(
        self,
        query_vector: List[float],
        query: str,
        filters: Dict[str, Any],
        limit: int,
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        """Performs RRF rank blending between semantic search and keyword searches."""
        vector_res = await self.vector_store.search_chunks(
            self.active_collection, query_vector, filters, limit * 2
        )
        lexical_res = await self._execute_lexical_search(query, filters, limit * 2)

        rrf_scores = {}
        doc_map = {}

        # Rank vectors
        for rank_idx, item in enumerate(vector_res):
            chunk_id = item.get("chunk_id")
            if chunk_id:
                doc_map[chunk_id] = item
                rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (
                    1.0 / (k + rank_idx + 1)
                )

        # Rank keywords
        for rank_idx, item in enumerate(lexical_res):
            chunk_id = item.get("chunk_id")
            if chunk_id:
                doc_map[chunk_id] = item
                rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (
                    1.0 / (k + rank_idx + 1)
                )

        fused = []
        for chunk_id, score in rrf_scores.items():
            item_copy = dict(doc_map[chunk_id])
            item_copy["rrf_score"] = score
            item_copy["similarity_score"] = (
                score  # Override similarity score with RRF metric
            )
            fused.append(item_copy)

        fused.sort(key=lambda x: x["similarity_score"], reverse=True)
        return fused[:limit]
