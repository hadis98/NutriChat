from __future__ import annotations

import re
from time import perf_counter as timer

import numpy as np
import torch
from rank_bm25 import BM25Okapi
from sentence_transformers import util

from nutrichat.config import RRF_K
from nutrichat.embeddings import embed_query
from nutrichat.reranking import rerank_candidates
from nutrichat.schemas import RetrievalOutput


def bm25_tokenize(text: str) -> list[str]:
    text = text.lower()
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", text)


def _max_or_none(values: list[float | None]) -> float | None:
    cleaned = [v for v in values if v is not None]
    return max(cleaned) if cleaned else None


class DenseRetriever:
    def __init__(self, chunks: list[dict], embeddings: torch.Tensor, embedding_model):
        self.chunks = chunks
        self.embeddings = embeddings
        self.embedding_model = embedding_model

    def retrieve(
        self,
        query: str,
        final_k: int = 3,
        candidate_k: int = 20,
        use_reranker: bool = True,
        reranker_model=None,
    ) -> RetrievalOutput:
        timing = {}

        start_query_embedding = timer()
        query_embedding = embed_query(query, self.embedding_model).to(self.embeddings.device)
        timing["query_embedding_seconds"] = timer() - start_query_embedding

        start_vector_search = timer()
        dot_scores = util.dot_score(query_embedding, self.embeddings)[0]
        timing["vector_search_seconds"] = timer() - start_vector_search

        k = min(candidate_k, len(self.chunks))
        start_topk = timer()
        candidate_scores, candidate_indices = torch.topk(input=dot_scores, k=k)
        timing["topk_seconds"] = timer() - start_topk

        candidates = []
        for rank, (score, idx) in enumerate(zip(candidate_scores, candidate_indices), start=1):
            item = self.chunks[int(idx)].copy()
            item["vector_score"] = float(score.detach().cpu())
            item["vector_rank"] = rank
            item.setdefault("bm25_score", None)
            item.setdefault("bm25_rank", None)
            item.setdefault("rrf_score", None)
            item.setdefault("retrieval_sources", ["dense"])
            candidates.append(item)

        top_vector_score = candidates[0]["vector_score"] if candidates else None

        rerank_seconds = 0.0
        if use_reranker and candidates:
            candidates, rerank_seconds = rerank_candidates(query, candidates, reranker_model)

        final_items = candidates[:final_k]
        timing["rerank_seconds"] = rerank_seconds
        retrieval_total_seconds = (
            timing["query_embedding_seconds"]
            + timing["vector_search_seconds"]
            + timing["topk_seconds"]
            + timing["rerank_seconds"]
        )

        return RetrievalOutput(
            context_items=final_items,
            retrieval_score_type="vector",
            retrieval_threshold_score=top_vector_score,
            top_vector_score=top_vector_score,
            top_bm25_score=None,
            top_hybrid_rrf_score=None,
            top_rerank_score=final_items[0].get("rerank_score") if final_items else None,
            top_final_vector_score=final_items[0].get("vector_score") if final_items else None,
            max_final_vector_score=_max_or_none([item.get("vector_score") for item in final_items]),
            top_final_bm25_score=None,
            max_final_bm25_score=None,
            top_final_hybrid_rrf_score=None,
            max_final_hybrid_rrf_score=None,
            query_embedding_seconds=timing["query_embedding_seconds"],
            vector_search_seconds=timing["vector_search_seconds"],
            topk_seconds=timing["topk_seconds"],
            rerank_seconds=timing["rerank_seconds"],
            retrieval_total_seconds=retrieval_total_seconds,
        )


class BM25Retriever:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.corpus = [bm25_tokenize(item["sentence_chunk"]) for item in chunks]
        self.bm25_model = BM25Okapi(self.corpus)

    def retrieve(
        self,
        query: str,
        final_k: int = 3,
        candidate_k: int = 20,
        use_reranker: bool = False,
        reranker_model=None,
    ) -> RetrievalOutput:
        timing = {"query_embedding_seconds": 0.0, "vector_search_seconds": 0.0}

        start_tokenize = timer()
        query_tokens = bm25_tokenize(query)
        timing["bm25_tokenize_seconds"] = timer() - start_tokenize

        start_bm25_search = timer()
        bm25_scores = self.bm25_model.get_scores(query_tokens)
        timing["bm25_search_seconds"] = timer() - start_bm25_search

        k = min(candidate_k, len(bm25_scores))
        start_topk = timer()
        candidate_indices = np.argsort(bm25_scores)[::-1][:k]
        timing["topk_seconds"] = timer() - start_topk

        candidates = []
        for rank, idx in enumerate(candidate_indices, start=1):
            item = self.chunks[int(idx)].copy()
            item["bm25_score"] = float(bm25_scores[int(idx)])
            item["bm25_rank"] = rank
            item.setdefault("vector_score", None)
            item.setdefault("vector_rank", None)
            item.setdefault("rrf_score", None)
            item.setdefault("retrieval_sources", ["bm25"])
            candidates.append(item)

        top_bm25_score = candidates[0]["bm25_score"] if candidates else None

        rerank_seconds = 0.0
        if use_reranker and candidates:
            candidates, rerank_seconds = rerank_candidates(query, candidates, reranker_model)

        final_items = candidates[:final_k]
        timing["rerank_seconds"] = rerank_seconds
        retrieval_total_seconds = (
            timing["bm25_tokenize_seconds"]
            + timing["bm25_search_seconds"]
            + timing["topk_seconds"]
            + timing["rerank_seconds"]
        )

        return RetrievalOutput(
            context_items=final_items,
            retrieval_score_type="bm25",
            retrieval_threshold_score=top_bm25_score,
            top_vector_score=None,
            top_bm25_score=top_bm25_score,
            top_hybrid_rrf_score=None,
            top_rerank_score=final_items[0].get("rerank_score") if final_items else None,
            top_final_vector_score=None,
            max_final_vector_score=None,
            top_final_bm25_score=final_items[0].get("bm25_score") if final_items else None,
            max_final_bm25_score=_max_or_none([item.get("bm25_score") for item in final_items]),
            top_final_hybrid_rrf_score=None,
            max_final_hybrid_rrf_score=None,
            query_embedding_seconds=0.0,
            vector_search_seconds=0.0,
            bm25_tokenize_seconds=timing["bm25_tokenize_seconds"],
            bm25_search_seconds=timing["bm25_search_seconds"],
            topk_seconds=timing["topk_seconds"],
            rerank_seconds=timing["rerank_seconds"],
            retrieval_total_seconds=retrieval_total_seconds,
        )


class HybridRRFRetriever:
    def __init__(self, dense_retriever: DenseRetriever, bm25_retriever: BM25Retriever, rrf_k: int = RRF_K):
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.rrf_k = rrf_k

    def _fuse(self, dense_items: list[dict], bm25_items: list[dict]) -> list[dict]:
        fused = {}

        for fallback_rank, item in enumerate(dense_items, start=1):
            chunk_id = item.get("chunk_id")
            if chunk_id is None:
                raise ValueError("Every chunk must have chunk_id before hybrid retrieval.")
            rank = item.get("vector_rank", fallback_rank)
            if chunk_id not in fused:
                fused_item = item.copy()
                fused_item["rrf_score"] = 0.0
                fused_item["retrieval_sources"] = []
                fused_item.setdefault("dense_rrf_rank", None)
                fused_item.setdefault("bm25_rrf_rank", None)
                fused_item.setdefault("bm25_score", None)
                fused_item.setdefault("bm25_rank", None)
                fused[chunk_id] = fused_item
            fused[chunk_id]["rrf_score"] += 1.0 / (self.rrf_k + rank)
            fused[chunk_id]["dense_rrf_rank"] = rank
            if "dense" not in fused[chunk_id]["retrieval_sources"]:
                fused[chunk_id]["retrieval_sources"].append("dense")

        for fallback_rank, item in enumerate(bm25_items, start=1):
            chunk_id = item.get("chunk_id")
            if chunk_id is None:
                raise ValueError("Every chunk must have chunk_id before hybrid retrieval.")
            rank = item.get("bm25_rank", fallback_rank)
            if chunk_id not in fused:
                fused_item = item.copy()
                fused_item["rrf_score"] = 0.0
                fused_item["retrieval_sources"] = []
                fused_item.setdefault("dense_rrf_rank", None)
                fused_item.setdefault("bm25_rrf_rank", None)
                fused_item.setdefault("vector_score", None)
                fused_item.setdefault("vector_rank", None)
                fused[chunk_id] = fused_item
            else:
                fused[chunk_id]["bm25_score"] = item.get("bm25_score")
                fused[chunk_id]["bm25_rank"] = item.get("bm25_rank")
            fused[chunk_id]["rrf_score"] += 1.0 / (self.rrf_k + rank)
            fused[chunk_id]["bm25_rrf_rank"] = rank
            if "bm25" not in fused[chunk_id]["retrieval_sources"]:
                fused[chunk_id]["retrieval_sources"].append("bm25")

        candidates = sorted(fused.values(), key=lambda item: item["rrf_score"], reverse=True)
        for rank, item in enumerate(candidates, start=1):
            item["hybrid_rank"] = rank
        return candidates

    def retrieve(
        self,
        query: str,
        final_k: int = 3,
        candidate_k: int = 20,
        use_reranker: bool = True,
        reranker_model=None,
    ) -> RetrievalOutput:
        dense_output = self.dense_retriever.retrieve(
            query=query,
            final_k=candidate_k,
            candidate_k=candidate_k,
            use_reranker=False,
            reranker_model=None,
        )
        bm25_output = self.bm25_retriever.retrieve(
            query=query,
            final_k=candidate_k,
            candidate_k=candidate_k,
            use_reranker=False,
            reranker_model=None,
        )

        start_topk = timer()
        candidates = self._fuse(dense_output.context_items, bm25_output.context_items)
        topk_seconds = timer() - start_topk

        top_hybrid_rrf_score = candidates[0].get("rrf_score") if candidates else None

        rerank_seconds = 0.0
        if use_reranker and candidates:
            candidates, rerank_seconds = rerank_candidates(query, candidates[:candidate_k], reranker_model)

        final_items = candidates[:final_k]
        retrieval_total_seconds = (
            dense_output.retrieval_total_seconds
            + bm25_output.retrieval_total_seconds
            + topk_seconds
            + rerank_seconds
        )

        return RetrievalOutput(
            context_items=final_items,
            retrieval_score_type="hybrid_rrf",
            retrieval_threshold_score=dense_output.top_vector_score,
            top_vector_score=dense_output.top_vector_score,
            top_bm25_score=bm25_output.top_bm25_score,
            top_hybrid_rrf_score=top_hybrid_rrf_score,
            top_rerank_score=final_items[0].get("rerank_score") if final_items else None,
            top_final_vector_score=final_items[0].get("vector_score") if final_items else None,
            max_final_vector_score=_max_or_none([item.get("vector_score") for item in final_items]),
            top_final_bm25_score=final_items[0].get("bm25_score") if final_items else None,
            max_final_bm25_score=_max_or_none([item.get("bm25_score") for item in final_items]),
            top_final_hybrid_rrf_score=final_items[0].get("rrf_score") if final_items else None,
            max_final_hybrid_rrf_score=_max_or_none([item.get("rrf_score") for item in final_items]),
            query_embedding_seconds=dense_output.query_embedding_seconds,
            vector_search_seconds=dense_output.vector_search_seconds,
            bm25_tokenize_seconds=bm25_output.bm25_tokenize_seconds,
            bm25_search_seconds=bm25_output.bm25_search_seconds,
            topk_seconds=dense_output.topk_seconds + bm25_output.topk_seconds + topk_seconds,
            rerank_seconds=rerank_seconds,
            retrieval_total_seconds=retrieval_total_seconds,
        )
