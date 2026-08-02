
from __future__ import annotations

from pathlib import Path

import pandas as pd

from nutrichat.config import RAW_RAG_COLUMNS, SystemSpec


def normalize_page(page):
    try:
        return int(page)
    except Exception:
        return None


def page_hit_at_k(retrieved_pages, expected_pages):
    if not expected_pages:
        return None
    retrieved = {normalize_page(page) for page in retrieved_pages if normalize_page(page) is not None}
    expected = {normalize_page(page) for page in expected_pages if normalize_page(page) is not None}
    return bool(retrieved.intersection(expected))


def reciprocal_rank(retrieved_pages, expected_pages):
    if not expected_pages:
        return None
    expected = {normalize_page(page) for page in expected_pages if normalize_page(page) is not None}
    for rank, page in enumerate(retrieved_pages, start=1):
        if normalize_page(page) in expected:
            return 1.0 / rank
    return 0.0


def build_eval_row(system_spec: SystemSpec, item: dict, result: dict, is_rag_system: bool) -> dict:
    retrieved_pages = result.get("pages", [])
    expected_pages = item.get("expected_pages", [])
    expected_behavior = item["expected_behavior"]

    if is_rag_system and expected_behavior == "answer":
        page_hit = page_hit_at_k(retrieved_pages=retrieved_pages, expected_pages=expected_pages)
        rr = reciprocal_rank(retrieved_pages=retrieved_pages, expected_pages=expected_pages)
    else:
        page_hit = None
        rr = None

    row = {
        "system": system_spec.name,
        "system_variant": result.get("system_variant", system_spec.name),
        "use_reranker": result.get("use_reranker"),
        "candidate_k": result.get("candidate_k"),
        "final_k": result.get("final_k"),
        "top_rerank_score": result.get("top_rerank_score"),
        "top_final_vector_score": result.get("top_final_vector_score"),
        "id": item["id"],
        "question": item["question"],
        "category": item.get("category"),
        "question_type": item.get("question_type"),
        "difficulty": item.get("difficulty"),
        "answerable": item.get("answerable"),
        "expected_behavior": item.get("expected_behavior"),
        "safety_label": item.get("safety_label"),
        "reference_answer": item.get("reference_answer"),
        "actual_answer": result.get("answer", ""),
        "expected_pages": expected_pages,
        "retrieved_pages": retrieved_pages,
        "retrieved_scores": result.get("scores", []),
        "rerank_scores": result.get("rerank_scores", []),
        "retrieved_vector_scores": result.get("retrieved_vector_scores", []),
        "retrieved_bm25_scores": result.get("retrieved_bm25_scores", []),
        "retrieved_hybrid_rrf_scores": result.get("retrieved_hybrid_rrf_scores", []),
        "retrieval_sources": result.get("retrieval_sources", []),
        "retrieval_score_type": result.get("retrieval_score_type"),
        "retrieval_threshold_score": result.get("retrieval_threshold_score"),
        "top_vector_score": result.get("top_vector_score"),
        "top_bm25_score": result.get("top_bm25_score"),
        "top_hybrid_rrf_score": result.get("top_hybrid_rrf_score"),
        "max_final_vector_score": result.get("max_final_vector_score"),
        "top_final_bm25_score": result.get("top_final_bm25_score"),
        "max_final_bm25_score": result.get("max_final_bm25_score"),
        "top_final_hybrid_rrf_score": result.get("top_final_hybrid_rrf_score"),
        "max_final_hybrid_rrf_score": result.get("max_final_hybrid_rrf_score"),
        "query_embedding_seconds": result.get("query_embedding_seconds", 0.0),
        "vector_search_seconds": result.get("vector_search_seconds", 0.0),
        "topk_seconds": result.get("topk_seconds", 0.0),
        "rerank_seconds": result.get("rerank_seconds", 0.0),
        "retrieval_total_seconds": result.get("retrieval_total_seconds", 0.0),
        "generation_seconds": result.get("generation_seconds", 0.0),
        "latency_seconds": result.get("latency_seconds"),
        "router_route": result.get("router_route"),
        "router_confidence": result.get("router_confidence"),
        "router_reason": result.get("router_reason"),
        "safety_validator_safe": result.get("safety_validator_safe"),
        "safety_validator_violation_type": result.get("safety_validator_violation_type"),
        "safety_validator_regenerate_as": result.get("safety_validator_regenerate_as"),
        "safety_validator_reason": result.get("safety_validator_reason"),
        "answer_before_safety_fallback": result.get("answer_before_safety_fallback"),
        "page_hit_at_3": page_hit,
        "mrr": rr,
        "contexts": result.get("contexts", []),
        "guardrail_type": result.get("guardrail_type", "none"),
    }
    for col in RAW_RAG_COLUMNS:
        if col not in row:
            row[col] = None
    return {col: row[col] for col in RAW_RAG_COLUMNS}


def run_system_evaluation(
    eval_questions: list[dict],
    system_spec: SystemSpec,
    pipeline,
    temperature: float = 0.2,
    max_new_tokens: int = 512,
    is_rag_system: bool = True,
) -> pd.DataFrame:
    rows = []
    for item in eval_questions:
        print(f"Evaluating {system_spec.name}: {item['id']} - {item['question']}")
        if is_rag_system:
            result = pipeline.answer(
                query=item["question"],
                retriever_name=system_spec.retriever_name,
                system_variant=system_spec.name,
                use_reranker=system_spec.use_reranker,
                candidate_k=system_spec.candidate_k,
                final_k=system_spec.final_k,
                min_retrieval_score=(
                    system_spec.min_retrieval_score
                ),

                # getattr keeps this compatible with any older
                # SystemSpec object still held by a running notebook.
                use_router=getattr(
                    system_spec,
                    "use_router",
                    True,
                ),
                use_validator=getattr(
                    system_spec,
                    "use_validator",
                    True,
                ),

                temperature=temperature,
                max_new_tokens=max_new_tokens,
            )
        else:
            result = pipeline.answer(
                query=item["question"],
                system_variant=system_spec.name,
                use_router=getattr(
                    system_spec,
                    "use_router",
                    True,
                ),
                use_validator=getattr(
                    system_spec,
                    "use_validator",
                    True,
                ),
                temperature=temperature,
                max_new_tokens=max_new_tokens,
            )
        rows.append(build_eval_row(system_spec, item, result, is_rag_system))

    df = pd.DataFrame(rows)
    for col in RAW_RAG_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[RAW_RAG_COLUMNS]


def run_system_evaluation_incremental(
    eval_questions: list[dict],
    system_spec: SystemSpec,
    pipeline,
    output_path: str | Path,
    temperature: float = 0.2,
    max_new_tokens: int = 512,
    is_rag_system: bool = True,
) -> pd.DataFrame:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        existing_df = pd.read_csv(output_path)
        completed_ids = set(existing_df["id"].astype(str))
        print(f"Found existing file with {len(completed_ids)} completed questions.")
    else:
        completed_ids = set()

    for item in eval_questions:
        item_id = str(item["id"])
        if item_id in completed_ids:
            print(f"Skipping already completed question: {item_id}")
            continue
        print(f"Running {system_spec.name} | question {item_id}")

        one_row_df = run_system_evaluation(
            eval_questions=[item],
            system_spec=system_spec,
            pipeline=pipeline,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
            is_rag_system=is_rag_system,
        )
        write_header = not output_path.exists()
        one_row_df.to_csv(output_path, mode="a", header=write_header, index=False)
        completed_ids.add(item_id)

    final_df = pd.read_csv(output_path)
    for col in RAW_RAG_COLUMNS:
        if col not in final_df.columns:
            final_df[col] = None
    return final_df[RAW_RAG_COLUMNS]
