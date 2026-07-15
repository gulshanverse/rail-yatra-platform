"""
Context Assembly: Prompts builders, token budget checkers, duplicates cleanup,
and Context Diversity Policy filters.
"""

import logging
from typing import Dict, Any, List

from app.knowledge.interfaces import IContextAssembler

logger = logging.getLogger("ai-service.knowledge.assembly")


class ContextAssembler(IContextAssembler):
    """Formats matching query contexts, deduplicates items, and enforces diversity limits."""

    def assemble_context(
        self, query: str, chunks: List[Dict[str, Any]], token_limit: int
    ) -> str:
        # 1. Deduplication (remove exact duplicates or semantic overlaps)
        seen_texts = set()
        unique_chunks = []
        for chunk in chunks:
            text = chunk.get("text", "").strip()
            if not text:
                continue
            if text not in seen_texts:
                seen_texts.add(text)
                unique_chunks.append(chunk)

        # 2. Context Diversity Policy filtering
        # Avoid clustering multiple chunks from a single document
        doc_counts = {}
        max_chunks_per_doc = 3
        diverse_chunks = []

        for chunk in unique_chunks:
            # Metadata can be nested or flat in testing payloads
            meta = chunk.get("metadata") or chunk
            doc_id = meta.get("document_id", "unknown_doc")

            doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1
            if doc_counts[doc_id] > max_chunks_per_doc:
                logger.info(
                    f"Diversity filter: Skipping chunk from '{doc_id}' (exceeded max {max_chunks_per_doc} limit)"
                )
                continue
            diverse_chunks.append(chunk)

        # 3. Approximate token counting (1 word approx 1.3 tokens) and budget packing
        assembled_blocks = []
        total_tokens = 0

        for chunk in diverse_chunks:
            meta = chunk.get("metadata") or chunk
            doc_id = meta.get("document_id", "unknown_doc")
            trust = meta.get("trust_score", 1.0)
            confidence = chunk.get("confidence_level", "MEDIUM")

            block_header = (
                f"[Source: {doc_id} | Trust Score: {trust} | Confidence: {confidence}]"
            )
            block_body = chunk.get("text", "")
            full_block = f"{block_header}\n{block_body}\n---\n"

            # Estimate token size
            estimated_tokens = int(len(full_block.split()) * 1.3)

            # Enforce budget limit
            if total_tokens + estimated_tokens > token_limit:
                logger.warning(
                    f"Context budget exceeded: truncating chunk {chunk.get('chunk_id')} to fit token limit"
                )
                break

            assembled_blocks.append(full_block)
            total_tokens += estimated_tokens

        final_context = "\n".join(assembled_blocks)
        logger.info(
            f"Assembled query context with {len(assembled_blocks)} unique blocks (Estimated tokens: {total_tokens}/{token_limit})"
        )
        return final_context
