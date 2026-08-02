import gradio as gr

from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

from nutrichat.config import (
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_NEW_TOKENS,
    K_CANDIDATES,
    N_RESOURCE_TO_RETURN,
    MIN_VECTOR_SCORE,
    MIN_BM25_SCORE,
)
from nutrichat.app.factory import create_pipeline, create_reranker
from nutrichat.app.formatting import (
    format_about_answer,
    format_diagnostics,
    format_quick_info,
    format_sources,
)


HIDE_SOURCE_GUARDRAILS = {
    "security_rule",
    "security_or_prompt_injection",
    "out_of_scope",
    "normal_no_context",
    "medical_no_context",
    "low_retrieval_score",
    "medical_low_retrieval_score",
    "refusal_after_validator",
    "medical_after_validator",
    "refusal_validator_fallback",
    "medical_validator_fallback",
}


HIDE_SOURCE_ROUTES = {
    "security_or_prompt_injection",
    "out_of_scope",
}


def should_show_sources(result: dict) -> bool:
    """Return True only when retrieved textbook context should be visible."""

    if not result:
        print("[SOURCE_DEBUG] hide: empty result", flush=True)
        return False

    print(
        "[SOURCE_DEBUG]",
        {
            "streaming": result.get("streaming"),
            "pending_safety_check": result.get("pending_safety_check"),
            "num_contexts": len(result.get("contexts") or []),
            "guardrail_type": result.get("guardrail_type"),
            "router_route": result.get("router_route"),
            "has_answer_before_safety_fallback": bool(
                result.get("answer_before_safety_fallback")
            ),
        },
        flush=True,
    )

    if result.get("streaming"):
        print("[SOURCE_DEBUG] hide: still streaming", flush=True)
        return False

    contexts = result.get("contexts") or []

    if not contexts:
        print("[SOURCE_DEBUG] hide: no contexts", flush=True)
        return False

    guardrail_type = result.get("guardrail_type")

    if guardrail_type in HIDE_SOURCE_GUARDRAILS:
        print(f"[SOURCE_DEBUG] hide: guardrail_type={guardrail_type}", flush=True)
        return False

    router_route = result.get("router_route")

    if router_route in HIDE_SOURCE_ROUTES:
        print(f"[SOURCE_DEBUG] hide: router_route={router_route}", flush=True)
        return False
    
    # If the safety validator replaced the model answer with a fallback,
    # do not show the retrieved context.
    if result.get("answer_before_safety_fallback"):
        print("[SOURCE_DEBUG] hide: answer was replaced by safety fallback", flush=True)
        return False

    print("[SOURCE_DEBUG] show sources", flush=True)
    return True

SYSTEM_OPTIONS = {
    "Dense RAG + reranker": {
        "retriever_name": "dense",
        "system_variant": "dense_rag_with_reranker",
        "use_reranker": True,
        "min_retrieval_score": MIN_VECTOR_SCORE,
    },
    "Dense RAG, no reranker": {
        "retriever_name": "dense",
        "system_variant": "dense_rag_no_reranker",
        "use_reranker": False,
        "min_retrieval_score": MIN_VECTOR_SCORE,
    },
    "BM25 RAG + reranker": {
        "retriever_name": "bm25",
        "system_variant": "bm25_rag_with_reranker",
        "use_reranker": True,
        "min_retrieval_score": MIN_BM25_SCORE,
    },
    "BM25 RAG, no reranker": {
        "retriever_name": "bm25",
        "system_variant": "bm25_rag_no_reranker",
        "use_reranker": False,
        "min_retrieval_score": MIN_BM25_SCORE,
    },
    "Hybrid RRF + reranker": {
        "retriever_name": "hybrid_rrf",
        "system_variant": "hybrid_dense_bm25_rrf_reranker",
        "use_reranker": True,
        "min_retrieval_score": MIN_VECTOR_SCORE,
    },
    "Hybrid RRF, no reranker": {
        "retriever_name": "hybrid_rrf",
        "system_variant": "hybrid_dense_bm25_rrf_no_reranker",
        "use_reranker": False,
        "min_retrieval_score": MIN_VECTOR_SCORE,
    },
}


class NutriChatAppService:
    def __init__(self):
        self.pipeline = create_pipeline()

    def ask(
        self,
        query: str,
        system_choice: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
        final_k: int = N_RESOURCE_TO_RETURN,
        candidate_k: int = K_CANDIDATES,
        use_streaming: bool = True,
    ):
        if not query or not query.strip():
            yield "Please enter a question.", ""
            return

        spec = SYSTEM_OPTIONS[system_choice]
        use_reranker = spec["use_reranker"]

        if use_reranker and self.pipeline.reranker_model is None:
            self.pipeline.reranker_model = create_reranker()

        def emit_result(result: dict):
            answer = result.get("answer", "")

            quick_info = format_quick_info(result)
            about_answer = format_about_answer(result)
            diagnostics = format_diagnostics(result)

            if result.get("streaming"):
                return (
                    answer,
                    "",
                    "<div class='empty-panel'>Diagnostics will appear after generation finishes.</div>",
                    quick_info,
                    about_answer,
                )

            if should_show_sources(result):
                sources_html = format_sources(result)
            else:
                sources_html = ""

            return (
                answer,
                sources_html,
                diagnostics,
                quick_info,
                about_answer,
            )

        try:
            common_kwargs = dict(
                query=query.strip(),
                retriever_name=spec["retriever_name"],
                system_variant=spec["system_variant"],
                use_reranker=use_reranker,
                candidate_k=int(candidate_k),
                final_k=int(final_k),
                min_retrieval_score=spec["min_retrieval_score"],
                temperature=float(temperature),
                max_new_tokens=int(max_new_tokens),
            )

            if use_streaming:
                for result in self.pipeline.answer_stream(**common_kwargs):
                    yield emit_result(result)
                return

            result = self.pipeline.answer(**common_kwargs)
            yield emit_result(result)

        except (APIConnectionError, APITimeoutError) as e:
            yield (
                "The retriever worked, but the generation API connection failed. "
                "This may be caused by a network issue or temporary API disconnect.\n\n"
                f"Error type: `{type(e).__name__}`",
                ""
            )

        except RateLimitError:
            yield (
                "The API rate limit was hit. Try again later or use a different API key.",
                ""
            )

        except APIStatusError as e:
            yield (
                f"The generation API returned HTTP `{e.status_code}`.",
                ""
            )

        except Exception as e:
            yield (
                f"Unexpected error:\n\n```text\n{type(e).__name__}: {e}\n```",
                ""
            )