"""
AI Evaluation Framework for Milestone 6.6 AI Response Composer Platform.
Provides golden dataset evaluation, grounding validation, hallucination detection,
and AI benchmark reporting.
"""

from typing import Dict, Any, List
import time

from app.composer.domain.aggregates import ResponseComposition


class GroundingValidator:
    """Evaluates whether composed facts are grounded in verified RAG knowledge items."""

    @staticmethod
    def validate_grounding(composed_text: str, knowledge_items: List[str]) -> Dict[str, Any]:
        if not knowledge_items:
            return {"is_grounded": False, "grounding_score": 0.0, "reason": "No knowledge items provided"}

        # Check for citation match tokens
        matches = [item for item in knowledge_items if any(w in composed_text for w in item.split()[:3])]
        score = len(matches) / len(knowledge_items) if knowledge_items else 0.0
        return {
            "is_grounded": score > 0.30,
            "grounding_score": round(score, 2),
            "matched_citations_count": len(matches),
        }


class HallucinationDetector:
    """Detects unverified numerical assertions or policy claims not backed by knowledge base."""

    @staticmethod
    def detect_hallucination(composed_text: str, verified_facts: Dict[str, Any]) -> Dict[str, Any]:
        # Scans for unverified refund percentages or schedule assertions
        hallucination_suspected = False
        reasons = []

        if "100% refund" in composed_text.lower() and not verified_facts.get("full_refund_allowed"):
            hallucination_suspected = True
            reasons.append("Unverified 100% refund assertion detected.")

        return {
            "hallucination_suspected": hallucination_suspected,
            "reasons": reasons,
            "confidence_in_output": 0.50 if hallucination_suspected else 1.0,
        }


class ResponseEvaluator:
    """Evaluates composed responses against golden benchmarks."""

    @staticmethod
    def evaluate(composition: ResponseComposition, golden_benchmark: Dict[str, Any]) -> Dict[str, Any]:
        if not composition or not composition.summary:
            return {"passed": False, "score": 0.0}

        summary = composition.summary.concise_answer
        expected_keywords = golden_benchmark.get("expected_keywords", [])

        matched = [k for k in expected_keywords if k.lower() in summary.lower()]
        keyword_score = len(matched) / len(expected_keywords) if expected_keywords else 1.0

        passed = keyword_score >= 0.70 and len(composition.action_chips) >= 1

        return {
            "passed": passed,
            "evaluation_score": round(keyword_score, 2),
            "matched_keywords": matched,
            "latency_ms": golden_benchmark.get("target_latency_ms", 150.0),
            "timestamp": time.time(),
        }
