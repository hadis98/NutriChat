from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import fitz
import numpy as np
import pandas as pd
from tqdm.auto import tqdm


def text_formatter(text: str) -> str:
    return text.replace("\n", " ").strip()


def open_and_read_pdf(pdf_path: str | Path, page_offset: int = -19) -> list[dict]:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    pages = []
    for page_number, page in tqdm(enumerate(doc), total=len(doc), desc="Reading PDF"):
        text = text_formatter(page.get_text())
        pages.append(
            {
                "page_number": page_number + page_offset,
                "page_char_count": len(text),
                "page_word_count": len(text.split()),
                "page_sentence_count_raw": len(text.split(". ")),
                "page_token_count": len(text) / 4,
                "text": text,
            }
        )
    return pages


def save_jsonl(rows: list[dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl(path: str | Path) -> list[dict]:
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def save_pickle(obj: Any, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(obj, f)


def load_pickle(path: str | Path) -> Any:
    with open(path, "rb") as f:
        return pickle.load(f)

def load_index_artifact(index_dir: str | Path) -> tuple[list[dict], np.ndarray]:
    index_dir = Path(index_dir)
    chunks = load_jsonl(index_dir / "chunks.jsonl")
    embeddings_np = np.load(index_dir / "embeddings.npy", allow_pickle=False).astype(np.float32)

    if len(chunks) != len(embeddings_np):
        raise ValueError("Chunk count does not match embedding count.")

    return chunks, embeddings_np


def load_eval_questions(path: str | Path) -> list[dict]:
    path = Path(path)
    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    if path.suffix.lower() == ".jsonl":
        return load_jsonl(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path).to_dict(orient="records")
    raise ValueError(f"Unsupported eval dataset format: {path}")


def save_dataframe(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def load_dataframe(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)
