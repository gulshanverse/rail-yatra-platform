"""
Chunking Engine: Pluggable splitters (Fixed size, Heading-aware, Sentence-boundary, and Hierarchical parent-child splits).
"""

import re
import logging
from typing import Dict, Any, List

from app.knowledge.interfaces import IChunkingStrategy
from app.knowledge.exceptions import ChunkingException
from app.knowledge.config import knowledge_settings

logger = logging.getLogger("ai-service.knowledge.chunking")


class FixedSizeChunkingStrategy(IChunkingStrategy):
    """Splits text content into standard token word boundaries with overlap offsets."""

    def __init__(self, chunk_size: int = None, overlap: int = None) -> None:
        self.chunk_size = chunk_size or knowledge_settings.CHUNK_SIZE
        self.overlap = overlap or knowledge_settings.CHUNK_OVERLAP
        if self.overlap >= self.chunk_size:
            raise ChunkingException("Overlap size must be less than chunk size")

    def split(self, text: str, doc_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            words = text.split()
            if not words:
                return []

            chunks = []
            doc_id = doc_metadata.get("document_id", "unknown_doc")
            step = self.chunk_size - self.overlap

            idx = 0
            for i in range(0, len(words), step):
                chunk_words = words[i : i + self.chunk_size]
                if not chunk_words:
                    break
                chunk_text = " ".join(chunk_words)

                chunk_id = f"{doc_id}_fixed_{idx}"
                chunk_meta = dict(doc_metadata)
                chunk_meta.update(
                    {
                        "chunk_id": chunk_id,
                        "chunking_strategy": "fixed_size",
                        "parent_document": doc_id,
                        "relationships": [],
                    }
                )

                chunks.append(
                    {
                        "document_id": doc_id,
                        "chunk_id": chunk_id,
                        "text": chunk_text,
                        "metadata": chunk_meta,
                    }
                )
                idx += 1

            return chunks
        except Exception as e:
            raise ChunkingException(f"Fixed size chunking split failed: {e}")


class HeadingAwareChunkingStrategy(IChunkingStrategy):
    """Splits markdown or structure documents at markdown headings (e.g. lines starting with #)."""

    def split(self, text: str, doc_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            doc_id = doc_metadata.get("document_id", "unknown_doc")
            lines = text.splitlines()

            chunks = []
            current_header = "Intro"
            current_lines = []
            idx = 0

            def save_chunk(
                header_title: str, text_lines: List[str], chunk_idx: int
            ) -> Dict[str, Any]:
                chunk_text = "\n".join(text_lines).strip()
                chunk_id = f"{doc_id}_header_{chunk_idx}"
                chunk_meta = dict(doc_metadata)
                chunk_meta.update(
                    {
                        "chunk_id": chunk_id,
                        "chunk_header": header_title,
                        "chunking_strategy": "heading_aware",
                        "parent_document": doc_id,
                        "relationships": [],
                    }
                )
                return {
                    "document_id": doc_id,
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "metadata": chunk_meta,
                }

            for line in lines:
                if line.startswith("#"):
                    if current_lines:
                        chunks.append(save_chunk(current_header, current_lines, idx))
                        idx += 1
                        current_lines = []
                    current_header = line.strip("# ")
                current_lines.append(line)

            if current_lines:
                chunks.append(save_chunk(current_header, current_lines, idx))

            return chunks
        except Exception as e:
            raise ChunkingException(f"Heading-aware chunking split failed: {e}")


class SemanticSentenceChunkingStrategy(IChunkingStrategy):
    """Splits text content grouping complete sentences and preventing splits mid-clause."""

    def split(self, text: str, doc_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            doc_id = doc_metadata.get("document_id", "unknown_doc")
            # Splitting text based on period, exclamation or question mark followed by whitespace
            sentences = re.split(r"(?<=[.!?])\s+", text)

            chunks = []
            current_chunk = []
            current_length = 0
            idx = 0

            for sentence in sentences:
                sentence_len = len(sentence.split())
                if current_length + sentence_len > knowledge_settings.CHUNK_SIZE:
                    if current_chunk:
                        chunk_text = " ".join(current_chunk)
                        chunk_id = f"{doc_id}_sentence_{idx}"
                        chunk_meta = dict(doc_metadata)
                        chunk_meta.update(
                            {
                                "chunk_id": chunk_id,
                                "chunking_strategy": "semantic_sentence",
                                "parent_document": doc_id,
                                "relationships": [],
                            }
                        )
                        chunks.append(
                            {
                                "document_id": doc_id,
                                "chunk_id": chunk_id,
                                "text": chunk_text,
                                "metadata": chunk_meta,
                            }
                        )
                        idx += 1
                        current_chunk = []
                        current_length = 0
                current_chunk.append(sentence)
                current_length += sentence_len

            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunk_id = f"{doc_id}_sentence_{idx}"
                chunk_meta = dict(doc_metadata)
                chunk_meta.update(
                    {
                        "chunk_id": chunk_id,
                        "chunking_strategy": "semantic_sentence",
                        "parent_document": doc_id,
                        "relationships": [],
                    }
                )
                chunks.append(
                    {
                        "document_id": doc_id,
                        "chunk_id": chunk_id,
                        "text": chunk_text,
                        "metadata": chunk_meta,
                    }
                )

            return chunks
        except Exception as e:
            raise ChunkingException(f"Semantic sentence chunking split failed: {e}")


class HierarchicalChunkingStrategy(IChunkingStrategy):
    """Divides content into larger parent chunks and smaller child chunks linked via relationships."""

    def __init__(self, parent_size: int = 1000, child_size: int = 200) -> None:
        self.parent_size = parent_size
        self.child_size = child_size

    def split(self, text: str, doc_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            doc_id = doc_metadata.get("document_id", "unknown_doc")
            words = text.split()
            if not words:
                return []

            chunks = []
            parent_idx = 0
            child_idx = 0

            # Split into parent elements
            for i in range(0, len(words), self.parent_size):
                parent_words = words[i : i + self.parent_size]
                parent_text = " ".join(parent_words)
                parent_id = f"{doc_id}_parent_{parent_idx}"

                parent_meta = dict(doc_metadata)
                parent_meta.update(
                    {
                        "chunk_id": parent_id,
                        "chunking_strategy": "hierarchical_parent",
                        "parent_document": doc_id,
                        "relationships": [],
                    }
                )

                # Append parent chunk
                chunks.append(
                    {
                        "document_id": doc_id,
                        "chunk_id": parent_id,
                        "text": parent_text,
                        "metadata": parent_meta,
                    }
                )

                # Split parent text into smaller child elements
                parent_words_list = parent_text.split()
                for j in range(0, len(parent_words_list), self.child_size):
                    child_words = parent_words_list[j : j + self.child_size]
                    child_text = " ".join(child_words)
                    child_id = f"{doc_id}_child_{child_idx}"

                    child_meta = dict(doc_metadata)
                    child_meta.update(
                        {
                            "chunk_id": child_id,
                            "chunking_strategy": "hierarchical_child",
                            "parent_document": doc_id,
                            "relationships": [
                                {"related_chunk_id": parent_id, "type": "child_of"}
                            ],
                        }
                    )

                    chunks.append(
                        {
                            "document_id": doc_id,
                            "chunk_id": child_id,
                            "text": child_text,
                            "metadata": child_meta,
                        }
                    )
                    child_idx += 1
                parent_idx += 1

            return chunks
        except Exception as e:
            raise ChunkingException(f"Hierarchical chunking split failed: {e}")


class ChunkingEngine:
    """Orchestrator invoking the selected split strategy."""

    def __init__(self, strategy: IChunkingStrategy = None) -> None:
        self.strategy = strategy or FixedSizeChunkingStrategy()

    def set_strategy(self, strategy: IChunkingStrategy) -> None:
        """Dynamically updates the split strategy config."""
        self.strategy = strategy

    def execute_chunking(
        self, text: str, doc_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Splits raw document text strings into rich chunk dictionaries."""
        if not text:
            return []
        return self.strategy.split(text, doc_metadata)
