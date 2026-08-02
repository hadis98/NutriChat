
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class RetrievalOutput:
    """Standard output returned by every retriever."""

    context_items: list[dict]
    retrieval_score_type: Optional[str] = None
    retrieval_threshold_score: Optional[float] = None

    top_vector_score: Optional[float] = None
    top_bm25_score: Optional[float] = None
    top_hybrid_rrf_score: Optional[float] = None

    top_rerank_score: Optional[float] = None
    top_final_vector_score: Optional[float] = None
    max_final_vector_score: Optional[float] = None

    top_final_bm25_score: Optional[float] = None
    max_final_bm25_score: Optional[float] = None

    top_final_hybrid_rrf_score: Optional[float] = None
    max_final_hybrid_rrf_score: Optional[float] = None

    query_embedding_seconds: float = 0.0
    vector_search_seconds: float = 0.0
    bm25_tokenize_seconds: float = 0.0
    bm25_search_seconds: float = 0.0
    topk_seconds: float = 0.0
    rerank_seconds: float = 0.0
    retrieval_total_seconds: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GenerationOutput:
    """Standard output returned by every generation pipeline."""

    question: str
    answer: str

    contexts: list[str] = field(default_factory=list)
    pages: list[Any] = field(default_factory=list)

    scores: list[Any] = field(default_factory=list)
    rerank_scores: list[Any] = field(default_factory=list)
    retrieved_vector_scores: list[Any] = field(default_factory=list)
    retrieved_bm25_scores: list[Any] = field(default_factory=list)
    retrieved_hybrid_rrf_scores: list[Any] = field(default_factory=list)
    retrieval_sources: list[Any] = field(default_factory=list)

    retrieval_score_type: Optional[str] = None
    retrieval_threshold_score: Optional[float] = None

    top_vector_score: Optional[float] = None
    top_bm25_score: Optional[float] = None
    top_hybrid_rrf_score: Optional[float] = None

    top_rerank_score: Optional[float] = None
    top_final_vector_score: Optional[float] = None
    max_final_vector_score: Optional[float] = None

    top_final_bm25_score: Optional[float] = None
    max_final_bm25_score: Optional[float] = None

    top_final_hybrid_rrf_score: Optional[float] = None
    max_final_hybrid_rrf_score: Optional[float] = None

    # Complete routing phase:
    # deterministic security check plus model router, when used.
    router_seconds: float = 0.0

    # Detailed retrieval measurements.
    query_embedding_seconds: float = 0.0
    vector_search_seconds: float = 0.0
    topk_seconds: float = 0.0

    # Retrieval before reranking.
    retrieval_seconds: float = 0.0

    # Reranker only.
    rerank_seconds: float = 0.0

    # Existing retrieval total, including reranking.
    # Retained for backward compatibility.
    retrieval_total_seconds: float = 0.0

    # Answer-generation API only.
    generation_seconds: float = 0.0

    # Post-generation safety-validation API only.
    safety_validation_seconds: float = 0.0

    # Complete wall-clock pipeline time.
    total_seconds: Optional[float] = None

    # Retained as an alias for old analysis code.
    latency_seconds: Optional[float] = None

    system_variant: Optional[str] = None
    use_reranker: Optional[bool] = None
    candidate_k: Optional[int] = None
    final_k: Optional[int] = None

    router_route: Optional[str] = None
    router_confidence: Optional[float] = None
    router_reason: Optional[str] = None

    safety_validator_safe: Optional[bool] = None
    safety_validator_violation_type: Optional[str] = None
    safety_validator_regenerate_as: Optional[str] = None
    safety_validator_reason: Optional[str] = None
    answer_before_safety_fallback: Optional[str] = None

    guardrail_type: str = "none"

    def to_dict(self) -> dict:
        return asdict(self)
