SYSTEM_OPTIONS_FOR_UI = [
    ("Research mode: Dense", "Dense RAG, no reranker"),
    ("Research mode: Dense + reranker", "Dense RAG + reranker"),
    ("Research mode: BM25", "BM25 RAG, no reranker"),
    ("Research mode: BM25 + reranker", "BM25 RAG + reranker"),
    ("Research mode: Hybrid", "Hybrid RRF, no reranker"),
    ("Research mode: Reranked hybrid", "Hybrid RRF + reranker"),
]

DEFAULT_SYSTEM_CHOICE = "Hybrid RRF, no reranker"
