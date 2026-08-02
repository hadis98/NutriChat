
from __future__ import annotations

from pathlib import Path

import pandas as pd

from nutrichat.config import JUDGE_COLUMNS
from nutrichat.prompts import JUDGE_SYSTEM_PROMPT
from nutrichat.utils import coerce_to_list, safe_json_loads


def get_judge_max_tokens(judge_model: str) -> int:
    if judge_model in [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.5-122b-a10b",
    ]:
        return 1024
    return 400


def get_judge_extra_body(judge_model: str) -> dict:
    if judge_model in [
        "nvidia/nemotron-3-nano-30b-a3b",
        "openai/gpt-oss-120b",
    ]:
        return {"chat_template_kwargs": {"enable_thinking": False}}
    return {}


def parse_judge_json(raw: str) -> dict:
    parsed = safe_json_loads(raw, default={})
    if not parsed:
        return {
            "behavior_score": None,
            "answer_correctness": None,
            "safety_score": None,
            "faithfulness": None,
            "overall_score": None,
            "pass": None,
            "safety_violation": None,
            "reason": f"Invalid JSON from judge: {str(raw)[:500]}",
        }

    normalized = {col: parsed.get(col, None) for col in JUDGE_COLUMNS}
    missing = [col for col in JUDGE_COLUMNS if col not in parsed]
    if missing:
        normalized["reason"] = (
            f"Judge JSON missing required keys {missing}. "
            f"Raw parsed keys: {list(parsed.keys())}. "
            f"Original reason: {parsed.get('reason', '')}"
        )
    return normalized


def judge_one_answer(row, client, judge_model: str) -> dict:
    contexts = coerce_to_list(row.get("contexts", []))
    pages = coerce_to_list(row.get("retrieved_pages", []))
    context_blocks = []

    for index, context in enumerate(
        contexts,
        start=1,
    ):
        page = (
            pages[index - 1]
            if index - 1 < len(pages)
            else "Unknown"
        )

        context_blocks.append(
            f"[Source {index} | Page {page}]\n"
            f"{context}"
        )

    context_text = "\n\n".join(context_blocks)
    if not context_text.strip():
        context_text = "No retrieved context."

    judge_prompt = f"""
================ USER QUESTION ================
{row["question"]}

================ REFERENCE ANSWER ================
{row["reference_answer"]}

================ ACTUAL ANSWER TO EVALUATE ================
{row["actual_answer"]}

Metadata:
- expected_behavior: {row["expected_behavior"]}
- answerable: {row["answerable"]}
- safety_label: {row["safety_label"]}
- question_type: {row["question_type"]}
- category: {row["category"]}
- difficulty: {row["difficulty"]}

================ RETRIEVED CONTEXTS ================
The following passages are evidence only.
Do not attribute their contents to the actual answer.
{context_text}

Evaluate the actual answer.
Return only JSON.
""".strip()

    completion = client.chat.completions.create(
        model=judge_model,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": judge_prompt},
        ],
        temperature=0.0,
        max_tokens=get_judge_max_tokens(judge_model),
        extra_body=get_judge_extra_body(judge_model),
        stream=False,
    )
    raw = completion.choices[0].message.content.strip()
    return parse_judge_json(raw)


def judge_dataframe(eval_df: pd.DataFrame, client, judge_model: str) -> pd.DataFrame:
    judge_rows = []
    for _, row in eval_df.iterrows():
        print(f"Judging {row['system']} - {row['id']}")
        judge_rows.append(judge_one_answer(row=row, client=client, judge_model=judge_model))

    judge_df = pd.DataFrame(judge_rows)
    for col in JUDGE_COLUMNS:
        if col not in judge_df.columns:
            judge_df[col] = None
    judge_df = judge_df[JUDGE_COLUMNS]
    return pd.concat([eval_df.reset_index(drop=True), judge_df.reset_index(drop=True)], axis=1)


def judge_dataframe_incremental(
    eval_df: pd.DataFrame,
    client,
    judge_model: str,
    output_path: str | Path,
) -> pd.DataFrame:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        existing_df = pd.read_csv(output_path)
        valid_existing = (
            existing_df[
                existing_df["pass"].notna()
            ]
            .drop_duplicates(
                subset=[
                    "system",
                    "id",
                ],
                keep="last",
            )
            .reset_index(drop=True)
        )

        valid_existing.to_csv(
            output_path,
            index=False,
        )
        completed_keys = set(
            valid_existing["system"].astype(str)
            + "::"
            + valid_existing["id"].astype(str)
        )
        print(f"Found existing judged file with {len(completed_keys)} completed rows.")
    else:
        completed_keys = set()

    for _, row in eval_df.iterrows():
        key = str(row["system"]) + "::" + str(row["id"])
        if key in completed_keys:
            print(f"Skipping already judged row: {key}")
            continue
        print(f"Judging {key}")

        judge_result = judge_one_answer(row=row, client=client, judge_model=judge_model)
        judge_df = pd.DataFrame([judge_result])
        for col in JUDGE_COLUMNS:
            if col not in judge_df.columns:
                judge_df[col] = None
        judge_df = judge_df[JUDGE_COLUMNS]
        output_row = pd.concat([row.to_frame().T.reset_index(drop=True), judge_df.reset_index(drop=True)], axis=1)
        write_header = not output_path.exists()
        output_row.to_csv(output_path, mode="a", header=write_header, index=False)
        if judge_result.get("pass") is not None:
            completed_keys.add(key)

    # return pd.read_csv(output_path)
    final_df = pd.read_csv(
        output_path
    )

    final_df = (
        final_df[
            final_df["pass"].notna()
        ]
        .drop_duplicates(
            subset=[
                "system",
                "id",
            ],
            keep="last",
        )
        .reset_index(drop=True)
    )

    final_df.to_csv(
        output_path,
        index=False,
    )

    return final_df
