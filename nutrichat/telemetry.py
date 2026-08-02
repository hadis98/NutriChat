from __future__ import annotations

import json
import threading
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from nutrichat.prompts import (
    JUDGE_SYSTEM_PROMPT,
    LLM_ONLY_SYSTEM_PROMPT,
    ROUTER_SYSTEM_PROMPT,
    SAFETY_VALIDATOR_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
)


ACTIVE_SYSTEM = ContextVar(
    "nutrichat_active_system",
    default="unknown",
)

_WRITE_LOCK = threading.Lock()


def _normalized_prompt(
    value: Any,
) -> str:
    return str(value or "").strip()


def classify_api_call(
    messages: list[dict] | None,
) -> str:
    messages = messages or []

    system_content = ""

    for message in messages:
        if message.get("role") == "system":
            system_content = _normalized_prompt(
                message.get("content")
            )
            break

    known_prompts = {
        _normalized_prompt(
            ROUTER_SYSTEM_PROMPT
        ): "router",

        _normalized_prompt(
            SAFETY_VALIDATOR_SYSTEM_PROMPT
        ): "validator",

        _normalized_prompt(
            JUDGE_SYSTEM_PROMPT
        ): "judge",

        _normalized_prompt(
            SYSTEM_PROMPT
        ): "generator",

        _normalized_prompt(
            LLM_ONLY_SYSTEM_PROMPT
        ): "generator",
    }

    return known_prompts.get(
        system_content,
        "other",
    )


def usage_value(
    usage: Any,
    field: str,
):
    if usage is None:
        return None

    if isinstance(usage, dict):
        return usage.get(field)

    return getattr(
        usage,
        field,
        None,
    )


def append_record(
    path: Path,
    record: dict,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    encoded = json.dumps(
        record,
        ensure_ascii=False,
    )

    with _WRITE_LOCK:
        with path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(encoded + "\n")


class LoggingCompletions:
    def __init__(
        self,
        wrapped,
        log_path: Path,
    ):
        self._wrapped = wrapped
        self._log_path = log_path

    def create(
        self,
        *args,
        **kwargs,
    ):
        started = perf_counter()

        model = kwargs.get(
            "model",
            "unknown",
        )

        messages = kwargs.get(
            "messages",
            [],
        )

        call_type = classify_api_call(
            messages
        )

        try:
            completion = (
                self._wrapped.create(
                    *args,
                    **kwargs,
                )
            )

        except Exception as error:
            append_record(
                self._log_path,
                {
                    "timestamp_utc": (
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                    ),
                    "system": (
                        ACTIVE_SYSTEM.get()
                    ),
                    "call_type": call_type,
                    "model": model,
                    "success": False,
                    "latency_seconds": (
                        perf_counter()
                        - started
                    ),
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "error_type": (
                        type(error).__name__
                    ),
                },
            )

            raise

        usage = getattr(
            completion,
            "usage",
            None,
        )

        append_record(
            self._log_path,
            {
                "timestamp_utc": (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
                "system": (
                    ACTIVE_SYSTEM.get()
                ),
                "call_type": call_type,
                "model": model,
                "success": True,
                "latency_seconds": (
                    perf_counter()
                    - started
                ),
                "input_tokens": usage_value(
                    usage,
                    "prompt_tokens",
                ),
                "output_tokens": usage_value(
                    usage,
                    "completion_tokens",
                ),
                "total_tokens": usage_value(
                    usage,
                    "total_tokens",
                ),
                "error_type": None,
            },
        )

        return completion

    def __getattr__(
        self,
        name: str,
    ):
        return getattr(
            self._wrapped,
            name,
        )


class LoggingChat:
    def __init__(
        self,
        wrapped,
        log_path: Path,
    ):
        self._wrapped = wrapped

        self.completions = (
            LoggingCompletions(
                wrapped.completions,
                log_path,
            )
        )

    def __getattr__(
        self,
        name: str,
    ):
        return getattr(
            self._wrapped,
            name,
        )


class UsageLoggingClient:
    def __init__(
        self,
        wrapped,
        log_path: str | Path,
    ):
        self._wrapped = wrapped
        self._log_path = Path(log_path)

        self.chat = LoggingChat(
            wrapped.chat,
            self._log_path,
        )

    def __getattr__(
        self,
        name: str,
    ):
        return getattr(
            self._wrapped,
            name,
        )