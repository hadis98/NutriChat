from __future__ import annotations

from sentence_transformers import CrossEncoder


def load_reranker(model_name: str, device: str) -> CrossEncoder:
    return CrossEncoder(model_name, device=device)


def rerank_candidates(
    query: str,
    candidates: list[dict],
    reranker_model: CrossEncoder | None,
    text_key: str = "sentence_chunk",
) -> tuple[list[dict], float]:
    if not candidates or reranker_model is None:
        return candidates, 0.0

    from time import perf_counter as timer

    pairs = [[query, item[text_key]] for item in candidates]
    start_rerank = timer()
    rerank_scores = reranker_model.predict(pairs)
    end_rerank = timer()

    output = []
    for item, rerank_score in zip(candidates, rerank_scores):
        new_item = item.copy()
        new_item["rerank_score"] = float(rerank_score)
        output.append(new_item)

    output = sorted(output, key=lambda x: x["rerank_score"], reverse=True)
    for rank, item in enumerate(output, start=1):
        item["rerank_rank"] = rank

    return output, end_rerank - start_rerank
