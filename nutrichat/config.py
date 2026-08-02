
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ============================================================
# Original notebook-compatible model settings
# ============================================================

GENERATION_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"

JUDGE_MODEL1 = "mistralai/mistral-medium-3.5-128b"
JUDGE_MODEL2 = "openai/gpt-oss-20b"
JUDGE_MODEL3 = "openai/gpt-oss-120b"
JUDGE_MODEL4 = "nvidia/nemotron-3-nano-30b-a3b"
JUDGE_MODEL = JUDGE_MODEL3

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"
ROUTER_MODEL = "openai/gpt-oss-120b"
BOOK_URL = "https://louis.pressbooks.pub/nutrition/open/download?type=pdf"
PDF_PAGE_OFFSET = -19


# ============================================================
# Original notebook-compatible retrieval settings
# ============================================================

ACTIVE_CHUNKING_STRATEGY = "sentence_15_no_overlap"
MIN_TOKEN_LENGTH = 30

USE_RERANKER = True
MIN_VECTOR_SCORE = None
N_RESOURCE_TO_RETURN = 3
K_CANDIDATES = 10
MIN_BM25_SCORE = None
RRF_K = 60

HYBRID_DENSE_CANDIDATES = K_CANDIDATES
HYBRID_BM25_CANDIDATES = K_CANDIDATES
HYBRID_RERANK_CANDIDATES = K_CANDIDATES

DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_NEW_TOKENS = 512


# ============================================================
# Canonical result schema matching the original notebook outputs
# ============================================================

RAW_RAG_COLUMNS = [
    "system",
    "system_variant",
    "use_reranker",
    "candidate_k",
    "final_k",
    "top_rerank_score",
    "top_final_vector_score",
    "id",
    "question",
    "category",
    "question_type",
    "difficulty",
    "answerable",
    "expected_behavior",
    "safety_label",
    "reference_answer",
    "actual_answer",
    "expected_pages",
    "retrieved_pages",
    "retrieved_scores",
    "rerank_scores",
    "retrieved_vector_scores",
    "retrieved_bm25_scores",
    "retrieved_hybrid_rrf_scores",
    "retrieval_sources",
    "retrieval_score_type",
    "retrieval_threshold_score",
    "top_vector_score",
    "top_bm25_score",
    "top_hybrid_rrf_score",
    "max_final_vector_score",
    "top_final_bm25_score",
    "max_final_bm25_score",
    "top_final_hybrid_rrf_score",
    "max_final_hybrid_rrf_score",
    "query_embedding_seconds",
    "vector_search_seconds",
    "topk_seconds",
    "rerank_seconds",
    "retrieval_total_seconds",
    "generation_seconds",
    "latency_seconds",
    "router_route",
    "router_confidence",
    "router_reason",
    "safety_validator_safe",
    "safety_validator_violation_type",
    "safety_validator_regenerate_as",
    "safety_validator_reason",
    "answer_before_safety_fallback",
    "page_hit_at_3",
    "mrr",
    "contexts",
    "guardrail_type",
]

JUDGE_COLUMNS = [
    "behavior_score",
    "answer_correctness",
    "safety_score",
    "faithfulness",
    "overall_score",
    "pass",
    "safety_violation",
    "reason",
]

JUDGED_RAG_COLUMNS = RAW_RAG_COLUMNS + JUDGE_COLUMNS


# ============================================================
# Dataclasses used by the experiment runner
# ============================================================

@dataclass(frozen=True)
class ModelConfig:
    generation_model: str = GENERATION_MODEL
    judge_model: str = JUDGE_MODEL
    embedding_model_name: str = EMBEDDING_MODEL
    reranker_model_name: Optional[str] = RERANKER_MODEL_NAME
    router_model: str = ROUTER_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS


@dataclass(frozen=True)
class RetrievalConfig:
    final_k: int = N_RESOURCE_TO_RETURN
    candidate_k: int = K_CANDIDATES
    use_reranker: bool = USE_RERANKER
    min_retrieval_score: Optional[float] = MIN_VECTOR_SCORE
    rrf_k: int = RRF_K


@dataclass(frozen=True)
class SystemSpec:
    name: str
    retriever_name: str
    use_reranker: bool

    candidate_k: int = K_CANDIDATES
    final_k: int = N_RESOURCE_TO_RETURN
    min_retrieval_score: Optional[float] = None

    # Pipeline-component switches.
    # Existing systems remain unchanged because both default to True.
    use_router: bool = True
    use_validator: bool = True

    temperature: float = DEFAULT_TEMPERATURE
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS

    experiment_group: str = "main"
    ablation_factor: str = "main_comparison"
    notes: str = ""
    
@dataclass(frozen=True)
class ExperimentConfig:
    model: ModelConfig = ModelConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    pdf_page_offset: int = PDF_PAGE_OFFSET
    random_seed: int = 42


MAIN_SYSTEMS = [
    SystemSpec(
        name="dense_rag_no_reranker",
        retriever_name="dense",
        use_reranker=False,
        candidate_k=K_CANDIDATES,
        final_k=N_RESOURCE_TO_RETURN,
        min_retrieval_score=MIN_VECTOR_SCORE,
    ),
    SystemSpec(
        name="dense_rag_with_reranker",
        retriever_name="dense",
        use_reranker=True,
        candidate_k=K_CANDIDATES,
        final_k=N_RESOURCE_TO_RETURN,
        min_retrieval_score=MIN_VECTOR_SCORE,
    ),
    SystemSpec(
        name="bm25_rag_no_reranker",
        retriever_name="bm25",
        use_reranker=False,
        candidate_k=K_CANDIDATES,
        final_k=N_RESOURCE_TO_RETURN,
        min_retrieval_score=MIN_BM25_SCORE,
    ),
    SystemSpec(
        name="bm25_rag_with_reranker",
        retriever_name="bm25",
        use_reranker=True,
        candidate_k=K_CANDIDATES,
        final_k=N_RESOURCE_TO_RETURN,
        min_retrieval_score=MIN_BM25_SCORE,
    ),
    SystemSpec(
        name="hybrid_dense_bm25_rrf_no_reranker",
        retriever_name="hybrid_rrf",
        use_reranker=False,
        candidate_k=K_CANDIDATES,
        final_k=N_RESOURCE_TO_RETURN,
        min_retrieval_score=MIN_VECTOR_SCORE,
    ),
    SystemSpec(
        name="hybrid_dense_bm25_rrf_reranker",
        retriever_name="hybrid_rrf",
        use_reranker=True,
        candidate_k=HYBRID_RERANK_CANDIDATES,
        final_k=N_RESOURCE_TO_RETURN,
        min_retrieval_score=MIN_VECTOR_SCORE,
    ),
]

# Extra ablation runs only. Baselines from MAIN_SYSTEMS should be reused in analysis.
ABLATION_EXTRA_SYSTEMS = [
    SystemSpec(
        name="ablation_hybrid_reranker_candidate_k_10",
        retriever_name="hybrid_rrf",
        use_reranker=True,
        candidate_k=10,
        final_k=N_RESOURCE_TO_RETURN,
        min_retrieval_score=MIN_VECTOR_SCORE,
        experiment_group="ablation",
        ablation_factor="candidate_k",
    ),
    SystemSpec(
        name="ablation_hybrid_reranker_candidate_k_30",
        retriever_name="hybrid_rrf",
        use_reranker=True,
        candidate_k=30,
        final_k=N_RESOURCE_TO_RETURN,
        min_retrieval_score=MIN_VECTOR_SCORE,
        experiment_group="ablation",
        ablation_factor="candidate_k",
    ),
    SystemSpec(
        name="ablation_hybrid_reranker_candidate_k_40",
        retriever_name="hybrid_rrf",
        use_reranker=True,
        candidate_k=40,
        final_k=N_RESOURCE_TO_RETURN,
        min_retrieval_score=MIN_VECTOR_SCORE,
        experiment_group="ablation",
        ablation_factor="candidate_k",
    ),
    SystemSpec(
        name="ablation_hybrid_reranker_final_k_1",
        retriever_name="hybrid_rrf",
        use_reranker=True,
        candidate_k=K_CANDIDATES,
        final_k=1,
        min_retrieval_score=MIN_VECTOR_SCORE,
        experiment_group="ablation",
        ablation_factor="final_k",
    ),
    SystemSpec(
        name="ablation_hybrid_reranker_final_k_5",
        retriever_name="hybrid_rrf",
        use_reranker=True,
        candidate_k=K_CANDIDATES,
        final_k=5,
        min_retrieval_score=MIN_VECTOR_SCORE,
        experiment_group="ablation",
        ablation_factor="final_k",
    ),
    SystemSpec(
        name="ablation_hybrid_reranker_final_k_8",
        retriever_name="hybrid_rrf",
        use_reranker=True,
        candidate_k=K_CANDIDATES,
        final_k=8,
        min_retrieval_score=MIN_VECTOR_SCORE,
        experiment_group="ablation",
        ablation_factor="final_k",
    ),
]


ALL_UNIQUE_SYSTEMS = MAIN_SYSTEMS + ABLATION_EXTRA_SYSTEMS
SYSTEMS = MAIN_SYSTEMS
