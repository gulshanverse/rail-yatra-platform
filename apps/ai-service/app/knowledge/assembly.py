"""
Context Assembly: Prompts builders, token budget checkers, and duplicates cleanup filters.
"""

import logging
from typing import Dict, Any, List

from app.knowledge.interfaces import IContextAssembler

logger = logging.getLogger("ai-service.knowledge.assembly")


class ContextAssembler(IContextAssembler):
    """Formats matching query contexts, deduplicates items, and enforces token budgets."""

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
            # Simple text identity deduplication
            if text not in seen_texts:
                seen_texts.add(text)
                unique_chunks.append(chunk)

        # 2. Approximate token counting (1 word approx 1.3 tokens)
        assembled_blocks = []
        total_tokens = 0

        # Build prompt section blocks
        for chunk in unique_chunks:
            meta = chunk.get("metadata", {})
            doc_id = meta.get("document_id", "unknown_doc")
            trust = meta.get("trust_score", 1.0)

            block_header = f"[Source: {doc_id} | Trust Score: {trust}]"
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
