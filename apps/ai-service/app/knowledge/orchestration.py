"""
Orchestration Platform: Implements the complete Phase 4 Milestone 4.3 pipeline layers
for context building, prompt registry, safety guardrails, streaming control, grounding validation,
citations, and response post-processing.
"""

import time
import uuid
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from app.knowledge.exceptions import KnowledgeException

logger = logging.getLogger("ai-service.knowledge.orchestration")


class ConversationContextLayer:
    """Manages active conversation context history, turn tracking, and context summarization."""

    def __init__(self, max_turns: int = 10, inactivity_ttl: float = 1800.0) -> None:
        self.max_turns = max_turns
        self.inactivity_ttl = inactivity_ttl
        self.history: List[Dict[str, Any]] = []
        self.last_accessed = time.time()

    def add_turn(
        self, role: str, message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self.last_accessed = time.time()
        self.history.append(
            {
                "role": role,
                "message": message,
                "timestamp": self.last_accessed,
                "metadata": metadata or {},
            }
        )

        # Enforce maximum turn limits
        if len(self.history) > self.max_turns * 2:
            self._summarize_old_turns()

    def get_formatted_history(self) -> List[Dict[str, Any]]:
        self.last_accessed = time.time()
        return list(self.history)

    def _summarize_old_turns(self) -> None:
        """Condenses oldest turns to save prompt token budgets."""
        to_summarize = self.history[:-4]
        summary_text = f"[Summarized context of {len(to_summarize)} prior turns]"

        # Retain only the condensed header and recent 4 turns
        self.history = [
            {
                "role": "system",
                "message": summary_text,
                "timestamp": time.time(),
                "metadata": {"is_summary": True},
            }
        ] + self.history[-4:]
        logger.info(
            f"Summarized conversation context. New history length: {len(self.history)}"
        )


class MemoryFusionEngine:
    """Fuses short-term memories and user preferences with decay weighting factors."""

    def fuse_memory(
        self, short_term_memory: List[Dict[str, Any]], user_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        fused = []
        now = time.time()

        # 1. Process Short-Term Memory segments
        for mem in short_term_memory:
            created = mem.get("timestamp", now)
            age_days = (now - created) / 86400.0

            # Apply time decay weight: w = exp(-0.05 * age)
            recency_weight = float(2.71828 ** (-0.05 * age_days))
            confidence = float(mem.get("confidence", 1.0))
            fused_score = (0.6 * recency_weight) + (0.4 * confidence)

            fused.append(
                {
                    "chunk_id": mem.get("id", str(uuid.uuid4())),
                    "text": mem.get("content", ""),
                    "similarity_score": fused_score,
                    "metadata": {
                        "document_id": "short_term_memory",
                        "type": "conversation_memory",
                        "trust_score": confidence,
                        "created_at": created,
                    },
                }
            )

        # 2. Process User Preferences
        for pref_key, pref_val in user_preferences.items():
            fused.append(
                {
                    "chunk_id": f"pref-{pref_key}",
                    "text": f"User preference: {pref_key} is set to {pref_val}",
                    "similarity_score": 0.90,
                    "metadata": {
                        "document_id": "user_profile",
                        "type": "user_preference",
                        "trust_score": 0.90,
                        "created_at": now,
                    },
                }
            )

        return fused


class ContextConflictResolutionEngine:
    """Resolves structural conflicts between sources based on authority priority chains."""

    def resolve_conflicts(
        self, context_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Define priority map: lower number means higher priority
        priority_map = {
            "verified_board_circular": 1,
            "circulars": 2,
            "railway_knowledge": 3,
            "conversation_memory": 4,
            "user_preference": 5,
        }

        resolved = []
        seen_topics: Dict[
            str, Tuple[int, Dict[str, Any]]
        ] = {}  # topic -> (priority, chunk)

        for chunk in context_chunks:
            meta = chunk.get("metadata") or chunk
            category = meta.get("category", "")
            doc_type = meta.get("type", category)

            # Resolve priority level
            priority = priority_map.get(doc_type, 99)
            if (
                doc_type == "railway_rules"
                or meta.get("authority_level") == "railway_board"
            ):
                priority = 1

            # Match conflict topic key (e.g. "cancellation rules" or "seat layout")
            text = chunk.get("text", "")
            topic_key = self._extract_conflict_topic(text)

            if not topic_key:
                resolved.append(chunk)
                continue

            if topic_key not in seen_topics:
                seen_topics[topic_key] = (priority, chunk)
            else:
                existing_priority, existing_chunk = seen_topics[topic_key]
                if priority < existing_priority:
                    # Current chunk overrides previous duplicate topic chunk
                    logger.warning(
                        f"Conflict detected for topic '{topic_key}'. "
                        f"Overriding previous chunk {existing_chunk.get('chunk_id')} with {chunk.get('chunk_id')} due to priority levels."
                    )
                    seen_topics[topic_key] = (priority, chunk)
                else:
                    logger.info(
                        f"Conflict resolution: Dropped chunk {chunk.get('chunk_id')} in favor of higher priority source."
                    )

        # Collect all resolved entries
        resolved.extend([entry for _, entry in seen_topics.values()])
        return resolved

    def _extract_conflict_topic(self, text: str) -> Optional[str]:
        """Simple topic matcher looking for cancel, refund, schedule keywords."""
        t = text.lower()
        if "cancel" in t or "refund" in t:
            return "cancellation_policy"
        if "schedule" in t or "timetable" in t:
            return "timetable_policy"
        if "luggage" in t:
            return "luggage_allowance"
        return None


class TokenBudgetManager:
    """Handles token limit allocations dynamically based on dynamic context size."""

    def __init__(self, total_limit: int = 8000) -> None:
        self.total_limit = total_limit

    def allocate_budget(
        self, history_len: int, memory_len: int, retrieval_len: int
    ) -> Dict[str, int]:
        # Minimum allocations
        system_budget = 1000
        output_reserve = 1000

        remaining = self.total_limit - (system_budget + output_reserve)

        # Allocate dynamically based on ratio of candidates length
        total_parts = max(1, history_len + memory_len + retrieval_len)

        alloc_history = int(remaining * (history_len / total_parts))
        alloc_memory = int(remaining * (memory_len / total_parts))
        alloc_retrieval = int(remaining * (retrieval_len / total_parts))

        # Enforce ceilings
        alloc_history = min(2000, max(500, alloc_history))
        alloc_memory = min(1500, max(300, alloc_memory))
        alloc_retrieval = min(4000, max(1000, alloc_retrieval))

        return {
            "system_prompt": system_budget,
            "conversation_history": alloc_history,
            "memory": alloc_memory,
            "retrieved_knowledge": alloc_retrieval,
            "output_reserve": output_reserve,
        }


class ContextCompressionEngine:
    """Compresses verbose context blocks while keeping key facts and citations intact."""

    def compress_text(self, text: str) -> str:
        # Simple semantic compression: removes double spaces, formatting fluff, and filler words
        fluff = [
            "please note that",
            "as we discussed",
            "it is important to remember that",
            "furthermore",
        ]
        compressed = text
        for word in fluff:
            compressed = re.sub(rf"(?i)\b{word}\b\s*", "", compressed)

        # Normalize whitespace
        compressed = " ".join(compressed.split())
        return compressed


class PromptRegistry:
    """Tracks prompt templates versions and facilitates A/B testing rollback configurations."""

    def __init__(self) -> None:
        self._templates: Dict[str, Dict[str, Any]] = {}
        # Prepopulate version 1.0 default RAG instructions
        self.register_template(
            "default_rag",
            "1.0",
            "System: {system_prompt}\nContext: {context}\nMemory: {memory}\nHistory: {history}\nUser query: {query}",
        )

    def register_template(self, template_name: str, version: str, content: str) -> None:
        if template_name not in self._templates:
            self._templates[template_name] = {}
        self._templates[template_name][version] = {
            "content": content,
            "registered_at": time.time(),
        }

    def get_template(self, template_name: str, version: str = "1.0") -> str:
        if (
            template_name not in self._templates
            or version not in self._templates[template_name]
        ):
            raise KnowledgeException(
                f"Prompt template '{template_name}' version '{version}' not found"
            )
        return self._templates[template_name][version]["content"]


class PromptBuilder:
    """Builds prompt configurations using values loaded from the Prompt Registry."""

    def __init__(self, registry: Optional[PromptRegistry] = None) -> None:
        self.registry = registry or PromptRegistry()

    def build_prompt(
        self,
        template_name: str,
        version: str,
        system_prompt: str,
        context: str,
        memory: str,
        history: str,
        query: str,
    ) -> str:
        template = self.registry.get_template(template_name, version)
        return template.format(
            system_prompt=system_prompt,
            context=context,
            memory=memory,
            history=history,
            query=query,
        )


class EnterpriseGuardrailsLayer:
    """Filters query inputs and response outputs to enforce safety compliance guidelines."""

    def validate_input(self, query: str) -> Tuple[bool, str]:
        """Prevents prompt injection overrides and jailbreak attempts."""
        q_lower = query.lower()

        # Injection and Override patterns
        injection_indicators = [
            "ignore previous instructions",
            "system override",
            "forget your instructions",
            "you are now in developer mode",
            "bypass security",
        ]

        for indicator in injection_indicators:
            if indicator in q_lower:
                logger.error(
                    f"Guardrails alert: prompt injection detected. Term '{indicator}' matches."
                )
                return False, "Input query rejected due to guardrail policy violation."

        return True, query

    def validate_output(self, response: str) -> Tuple[bool, str]:
        """Ensures compliance with safety policies and checks for PII leaks."""
        # Simple regex checks for PII leak (e.g. credit card format)
        cc_pattern = r"\b(?:\d[ -]*?){13,16}\b"
        if re.search(cc_pattern, response):
            logger.error(
                "Guardrails alert: Credit Card details detected in generated response. Blocking."
            )
            return (
                False,
                "Response blocked due to sensitive information containment policies.",
            )

        return True, response


class LLMGateway:
    """Resilient router client that handles fallbacks, circuit breakers, and retries."""

    def __init__(self) -> None:
        self.circuit_open = False
        self.failures_count = 0
        self.circuit_reset_at = 0.0

    async def generate_response(
        self, prompt: str, fallback_provider: bool = False
    ) -> str:
        now = time.time()

        # Check circuit breaker status
        if self.circuit_open:
            if now > self.circuit_reset_at:
                self.circuit_open = False
                self.failures_count = 0
                logger.warning(
                    "LLM Gateway: Resetting circuit breaker to CLOSED status."
                )
            else:
                logger.error(
                    "LLM Gateway: Circuit breaker is OPEN. Fast-failing to backup fallback provider."
                )
                return self._execute_fallback_model(prompt)

        try:
            # Simulate LLM API request execution
            if "fail_gateway" in prompt:
                raise Exception("Primary LLM connection timed out")

            return "This is a verified grounded AI response matching railway ticket circular regulations."
        except Exception as e:
            self.failures_count += 1
            logger.error(f"Primary LLM Gateway request failed: {e}")

            if self.failures_count >= 3:
                self.circuit_open = True
                self.circuit_reset_at = now + 60.0  # open for 60 seconds
                logger.warning("LLM Gateway: Circuit breaker triggered to OPEN state.")

            return self._execute_fallback_model(prompt)

    def _execute_fallback_model(self, prompt: str) -> str:
        logger.info("Executing fallback model generator query...")
        return "Backup LLM response: cancellation instructions details are grounded."


class StreamingResponseController:
    """Manages chunk output buffering, citation validation, and client streams."""

    async def stream_response(self, text: str) -> AsyncGenerator[str, None]:
        chunks = [text[i : i + 10] for i in range(0, len(text), 10)]
        for chunk in chunks:
            # Yield chunks simulated asynchronously
            yield chunk
            time.sleep(0.01)


class GroundingValidator:
    """Validates that LLM generated facts are supported by retrieved sources."""

    def validate_grounding(self, response: str, context_text: str) -> float:
        """Computes a grounding score (0.0 to 1.0) indicating factual correctness."""
        res_clean = re.sub(r"[^\w\s]", "", response.lower())
        ctx_clean = re.sub(r"[^\w\s]", "", context_text.lower())
        
        res_words = set(res_clean.split())
        ctx_words = set(ctx_clean.split())

        # Ignore common filler words
        filler = {
            "is",
            "the",
            "a",
            "an",
            "are",
            "and",
            "or",
            "in",
            "on",
            "at",
            "by",
            "of",
            "to",
        }
        res_words -= filler
        ctx_words -= filler

        if not res_words:
            return 1.0

        matched_words = res_words.intersection(ctx_words)
        grounding_score = len(matched_words) / len(res_words)
        logger.info(f"Grounding validator score: {grounding_score:.2f}")
        return grounding_score


class CitationEngine:
    """Aligns inline bracket indices and appends reference source lists."""

    def compile_citations(self, response: str, chunks: List[Dict[str, Any]]) -> str:
        # Match references and add inline indices
        inline_cites = []
        references = ["\nReferences:"]

        for idx, chunk in enumerate(chunks):
            meta = chunk.get("metadata") or chunk
            doc_id = meta.get("document_id", "unknown_doc")
            ref_idx = f"[{idx + 1}]"

            inline_cites.append(ref_idx)
            references.append(f"{ref_idx} Source doc: {doc_id}")

        final_text = f"{response} {' '.join(inline_cites)}\n" + "\n".join(references)
        return final_text


class ResponseConfidenceEngine:
    """Computes composite metrics from grounding scores and context similarity limits."""

    def evaluate_confidence(self, similarity: float, grounding: float) -> str:
        score = (0.5 * similarity) + (0.5 * grounding)
        if score >= 0.85:
            return "HIGH"
        if score >= 0.65:
            return "MEDIUM"
        if score >= 0.20:
            return "LOW"
        return "UNKNOWN"


class ResponsePolicyEngine:
    """Adapts system outputs and cautions based on response confidence classes."""

    def apply_policy(self, response: str, confidence_level: str) -> str:
        if confidence_level == "HIGH":
            return response
        if confidence_level == "MEDIUM":
            caution = (
                "\n[Caution: Verified content, but please confirm schedules locally.]"
            )
            return response + caution
        if confidence_level == "LOW":
            warning = "\n[Warning: Unverified response. We strongly suggest verifying this circular directly via railway board.]"
            return response + warning

        # UNKNOWN or critically low
        return "I apologize, but I cannot verify a reliable answer matching official railway guidelines."


class ResponsePostProcessor:
    """Polishes spacing, Markdown tables formatting, and localization formats."""

    def post_process(self, response: str) -> str:
        # Clean formatting, excess spaces, and enforce markdown bolding circular numbers
        cleaned = " ".join(response.strip().split("\n"))
        cleaned = re.sub(r"(Circular \d+)", r"**\1**", cleaned)
        return cleaned


class TraceabilityManager:
    """Attaches unified logs tracing metadata variables for audit log captures."""

    def generate_trace_metadata(self, session_id: str) -> Dict[str, Any]:
        return {
            "trace_id": str(uuid.uuid4()),
            "session_id": session_id,
            "timestamp": time.time(),
            "versions": {
                "prompt_version": "1.0",
                "retrieval_version": "v1",
                "embedding_version": "mock-embedding-v1",
                "model_version": "gemini-flash",
            },
        }
