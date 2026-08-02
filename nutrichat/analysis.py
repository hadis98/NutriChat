from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd

from nutrichat.config import JUDGED_RAG_COLUMNS, RAW_RAG_COLUMNS


def load_many_csvs(pattern: str) -> pd.DataFrame:
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No CSV files matched: {pattern}")
    dfs = []
    for path in paths:
        df = pd.read_csv(path)
        df["source_file"] = Path(path).name
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def validate_raw_schema(df: pd.DataFrame) -> dict:
    return {
        "missing": [c for c in RAW_RAG_COLUMNS if c not in df.columns],
        "extra": [c for c in df.columns if c not in RAW_RAG_COLUMNS],
    }


def validate_judged_schema(df: pd.DataFrame) -> dict:
    return {
        "missing": [c for c in JUDGED_RAG_COLUMNS if c not in df.columns],
        "extra": [c for c in df.columns if c not in JUDGED_RAG_COLUMNS],
    }


def summarize_overall(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("system")
        .agg(
            n=("id", "count"),
            mean_overall_score=("overall_score", "mean"),
            pass_rate=("pass", "mean"),
            safety_violation_rate=("safety_violation", "mean"),
            avg_latency=("latency_seconds", "mean"),
            page_hit_rate=("page_hit_at_3", "mean"),
            mean_mrr=("mrr", "mean"),
        )
        .reset_index()
        .sort_values("pass_rate", ascending=False)
    )


def summarize_by_behavior(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["system", "expected_behavior"])
        .agg(
            n=("id", "count"),
            mean_overall_score=("overall_score", "mean"),
            pass_rate=("pass", "mean"),
            safety_violation_rate=("safety_violation", "mean"),
            avg_latency=("latency_seconds", "mean"),
            page_hit_rate=("page_hit_at_3", "mean"),
            mean_mrr=("mrr", "mean"),
        )
        .reset_index()
    )


def summarize_ablations(df: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "system",
        "retrieval_score_type",
        "use_reranker",
        "candidate_k",
        "final_k",
    ]
    available_group_cols = [col for col in group_cols if col in df.columns]
    return (
        df.groupby(available_group_cols)
        .agg(
            n=("id", "count"),
            mean_overall_score=("overall_score", "mean"),
            pass_rate=("pass", "mean"),
            safety_violation_rate=("safety_violation", "mean"),
            avg_latency=("latency_seconds", "mean"),
            page_hit_rate=("page_hit_at_3", "mean"),
            mean_mrr=("mrr", "mean"),
        )
        .reset_index()
        .sort_values("pass_rate", ascending=False)
    )


def show_failures(df: pd.DataFrame, system_name: str | None = None, expected_behavior: str | None = None) -> pd.DataFrame:
    out = df[df["pass"] == False].copy()
    if system_name is not None:
        out = out[out["system"] == system_name]
    if expected_behavior is not None:
        out = out[out["expected_behavior"] == expected_behavior]
    cols = [
        "system",
        "id",
        "expected_behavior",
        "question_type",
        "difficulty",
        "question",
        "reference_answer",
        "actual_answer",
        "overall_score",
        "reason",
        "retrieved_pages",
        "expected_pages",
        "page_hit_at_3",
        "mrr",
    ]
    return out[[c for c in cols if c in out.columns]]
