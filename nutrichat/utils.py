
from __future__ import annotations

import ast
import json
import textwrap
from pathlib import Path
from typing import Any


def ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def print_wrapped(text: str, width: int = 80) -> None:
    print(textwrap.fill(str(text), width=width))


def safe_json_loads(raw: str, default: dict | None = None) -> dict:
    if default is None:
        default = {}
    if raw is None:
        return default
    raw = str(raw).strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def coerce_to_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        for parser in (json.loads, ast.literal_eval):
            try:
                parsed = parser(stripped)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
        return [value]
    return [value]


def require_columns(df, columns: list[str], name: str = "DataFrame") -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")
