from __future__ import annotations

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def load_embedding_model(model_name: str, device: str) -> SentenceTransformer:
    return SentenceTransformer(model_name, device=device)


def embed_query(query: str, model: SentenceTransformer):
    query_text = BGE_QUERY_PREFIX + query
    return model.encode(
        query_text,
        convert_to_tensor=True,
        normalize_embeddings=True,
    )


def embed_chunks(
    chunks: list[dict],
    model: SentenceTransformer,
    batch_size: int = 64,
    show_progress_bar: bool = True,
) -> np.ndarray:
    texts_to_embed = [item["embedding_text"] for item in chunks]
    embeddings_np = model.encode(
        texts_to_embed,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=show_progress_bar,
    )
    return embeddings_np.astype(np.float32)


def attach_embeddings_to_chunks(chunks: list[dict], embeddings_np: np.ndarray) -> list[dict]:
    if len(chunks) != len(embeddings_np):
        raise ValueError(
            f"Number of chunks ({len(chunks)}) does not match embeddings ({len(embeddings_np)})."
        )
    output = []
    for item, embedding in zip(chunks, embeddings_np):
        new_item = item.copy()
        new_item["embedding"] = embedding.astype(np.float32)
        output.append(new_item)
    return output


def tensor_from_chunk_embeddings(chunks: list[dict], device: str) -> torch.Tensor:
    if not chunks or "embedding" not in chunks[0]:
        raise ValueError("Chunks must contain an 'embedding' key. Run embed_chunks first.")
    return torch.tensor(
        np.array([item["embedding"] for item in chunks]),
        dtype=torch.float32,
    ).to(device)
