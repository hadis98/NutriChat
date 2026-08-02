from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import httpx
import torch
from openai import OpenAI

from nutrichat.config import (
    EMBEDDING_MODEL,
    GENERATION_MODEL,
    ROUTER_MODEL,
    RRF_K,
)
from nutrichat.data import load_index_artifact
from nutrichat.embeddings import load_embedding_model
from nutrichat.generation import RAGPipeline
from nutrichat.reranking import load_reranker
from nutrichat.retrievers import DenseRetriever, BM25Retriever, HybridRRFRetriever
from nutrichat.safety import SafetyRouter


NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

ARTIFACT_DIR = Path(
    "artifacts/index_sentence_15_no_overlap"
)


def create_client() -> OpenAI:
    api_key = os.getenv("NVIDIA_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Missing NVIDIA_API_KEY. Add it to your .env file locally "
            "or add it as a Hugging Face Space secret."
        )

    return OpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=api_key,
        max_retries=2,
        http_client=httpx.Client(
            timeout=httpx.Timeout(120.0, connect=20.0),
        ),
    )


def get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"

@lru_cache(maxsize=1)
def create_reranker():
    device = get_device()
    # Small reranker for CPU-friendly Gradio deployment.
    RERANKER_MODEL_NAME = "mixedbread-ai/mxbai-rerank-xsmall-v1"
    print(f"[INFO] Loading reranker model: {RERANKER_MODEL_NAME}...", flush=True)
    print(f"[INFO] Lazy-loading reranker model: {RERANKER_MODEL_NAME}", flush=True)
    print(f"[INFO] Reranker device: {device}", flush=True)

    reranker_model = load_reranker(RERANKER_MODEL_NAME, device=device)

    print("[INFO] Reranker model loaded.", flush=True)

    return reranker_model


@lru_cache(maxsize=1)
def create_pipeline() -> RAGPipeline:
    device = get_device()
    print(f"[INFO] Using device: {device}")

    client = create_client()

    chunks, embeddings_np = load_index_artifact(ARTIFACT_DIR)
    print(f"[INFO] Loaded {len(chunks)} chunks from {ARTIFACT_DIR}")
    print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL}...", flush=True)
    embedding_model = load_embedding_model(EMBEDDING_MODEL, device=device)
    print("[INFO] Loading chunk embeddings into tensor...", flush=True)
    embeddings = torch.tensor(embeddings_np, dtype=torch.float32).to(device)

    print("[INFO] Building dense retriever...", flush=True)
    dense_retriever = DenseRetriever(
        chunks=chunks,
        embeddings=embeddings,
        embedding_model=embedding_model,
    )

    print("[INFO] Building BM25 retriever...", flush=True)
    bm25_retriever = BM25Retriever(chunks=chunks)

    print("[INFO] Building hybrid RRF retriever...", flush=True)
    hybrid_retriever = HybridRRFRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        rrf_k=RRF_K,
    )

    print("[INFO] Creating RAG pipeline...", flush=True)
    return RAGPipeline(
        client=client,
        generation_model=os.getenv("MODEL_NAME", GENERATION_MODEL),
        retrievers={
            "dense": dense_retriever,
            "bm25": bm25_retriever,
            "hybrid_rrf": hybrid_retriever,
        },
        reranker_model=None,
        safety_router=SafetyRouter(
            client, 
            router_model=os.getenv(
                "ROUTER_MODEL_NAME", 
                ROUTER_MODEL
            )
        ),
    )
