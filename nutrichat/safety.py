
from __future__ import annotations

import re
from functools import lru_cache

from nutrichat.config import ROUTER_MODEL
from nutrichat.prompts import ROUTER_SYSTEM_PROMPT, SAFETY_VALIDATOR_SYSTEM_PROMPT
from nutrichat.utils import safe_json_loads

SECURITY_PATTERNS = [
    r"ignore (all )?(previous|prior|above) instructions",
    r"system prompt",
    r"developer message",
    r"hidden prompt",
    r"internal instruction",
    r"api key",
    r"reveal.*(prompt|instruction|schema|label|answer key)",
    r"print.*(prompt|instruction|source code)",
]

PROMPT_LEAK_PATTERNS = [
    r"system prompt",
    r"developer message",
    r"hidden instruction",
    r"internal instruction",
    r"api key",    
]

class SafetyRouter:
    def __init__(self, client, router_model: str = ROUTER_MODEL):
        self.client = client
        self.router_model = router_model

    @staticmethod
    def is_query_sensitive(query: str) -> bool:
        lowered = query.lower()
        return any(re.search(pattern, lowered) for pattern in SECURITY_PATTERNS)

    @staticmethod
    def has_prompt_leak(answer: str) -> bool:
        lowered = answer.lower()
        return any(re.search(pattern, lowered) for pattern in PROMPT_LEAK_PATTERNS)

    @lru_cache(maxsize=4096)
    def classify_query_intent(self, query: str) -> dict:
        user_prompt = f"""
Classify the following user question.

User question:
<<<
{query}
>>>

Return only the JSON object.
""".strip()
        completion = self.client.chat.completions.create(
            model=self.router_model,
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=256,
            extra_body={
                "chat_template_kwargs": {
                    "enable_thinking": False,
                }
            },
            stream=False,
        )
        raw = completion.choices[0].message.content
        result = safe_json_loads(
            raw,
            default={
                "route": "security_or_prompt_injection",
                "confidence": 0.0,
                "reason": f"Router returned invalid JSON: {str(raw)[:300]}",
            },
        )
        valid_routes = {
            "normal_nutrition_qa",
            "personal_medical_safety",
            "security_or_prompt_injection",
            "out_of_scope",
        }
        if result.get("route") not in valid_routes:
            result = {
                "route": "normal_nutrition_qa",
                "confidence": 0.0,
                "reason": "Invalid route returned by router.",
            }
        return result

    def deterministic_runtime_safety_check(self, query: str, answer: str, route: str) -> dict:
        if self.has_prompt_leak(answer):
            return {
                "safe": False,
                "violation_type": "security_disclosure",
                "should_regenerate_as": "medical_safe" if route == "personal_medical_safety" else "refusal",
                "reason": "Answer appears to reveal or echo prompt/system instructions.",
            }
        return {
            "safe": True,
            "violation_type": "none",
            "should_regenerate_as": "none",
            "reason": "No deterministic runtime violation found.",
        }

    def validate_answer_safety(self, query: str, answer: str, route: str) -> dict:
        deterministic_result = self.deterministic_runtime_safety_check(query, answer, route)
        if not deterministic_result.get("safe", True):
            return deterministic_result

        prompt = f"""
User question:
{query}

Router route:
{route}

Model answer:
{answer}

Validate the answer.
Return only one valid JSON object.
""".strip()
        completion = self.client.chat.completions.create(
            model=self.router_model,
            messages=[
                {"role": "system", "content": SAFETY_VALIDATOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=256,
            extra_body={
                "chat_template_kwargs": {
                    "enable_thinking": False,
                }
            },
            stream=False,
        )
        raw = completion.choices[0].message.content
        result = safe_json_loads(raw, default={})
        required = {"safe", "violation_type", "should_regenerate_as", "reason"}
        if not required.issubset(result.keys()):
            return {
                "safe": False,
                "violation_type": "validator_failure",
                "should_regenerate_as": "medical_safe" if route == "personal_medical_safety" else "refusal",
                "reason": "Validator returned invalid JSON; using conservative fallback.",
            }
        return result
