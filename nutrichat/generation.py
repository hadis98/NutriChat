
from __future__ import annotations

from time import perf_counter

from nutrichat.config import GENERATION_MODEL, MIN_VECTOR_SCORE, N_RESOURCE_TO_RETURN, K_CANDIDATES
from nutrichat.prompts import (
    LLM_ONLY_OUT_OF_SCOPE_RESPONSE,
    LLM_ONLY_SYSTEM_PROMPT,
    MEDICAL_SAFE_RESPONSE,
    OUT_OF_SCOPE_RESPONSE,
    SYSTEM_PROMPT,
    build_llm_only_prompt,
    build_rag_prompt,
)
from nutrichat.safety import SafetyRouter
from nutrichat.schemas import GenerationOutput, RetrievalOutput


def _score_list(context_items: list[dict], retrieval_score_type: str | None) -> list:
    if retrieval_score_type == "bm25":
        return [item.get("bm25_score") for item in context_items]
    if retrieval_score_type == "hybrid_rrf":
        return [item.get("rrf_score") for item in context_items]
    return [item.get("vector_score") for item in context_items]


class RAGPipeline:
    def __init__(
        self,
        client,
        generation_model: str = GENERATION_MODEL,
        retrievers: dict | None = None,
        reranker_model=None,
        safety_router: SafetyRouter | None = None,
    ):
        self.client = client
        self.generation_model = generation_model
        self.retrievers = retrievers or {}
        self.reranker_model = reranker_model
        self.safety_router = safety_router or SafetyRouter(client)

    def _guardrail_output(
        self,
        query: str,
        answer: str,
        guardrail_type: str,
        system_variant: str | None,
        use_reranker: bool | None,
        candidate_k: int | None,
        final_k: int | None,
        start_total: float,
        router_route: str | None = None,
        router_confidence: float | None = None,
        router_reason: str | None = None,
        safety_reason: str | None = None,
        router_seconds: float = 0.0,
        retrieval_seconds: float = 0.0,
        rerank_seconds: float = 0.0,
        retrieval_total_seconds: float = 0.0,
        generation_seconds: float = 0.0,
        safety_validation_seconds: float = 0.0,
    ) -> dict:
        total_seconds = (
            perf_counter()
            - start_total
        )

        return GenerationOutput(
            question=query,
            answer=answer,
            system_variant=system_variant,
            use_reranker=use_reranker,
            candidate_k=candidate_k,
            final_k=final_k,

            router_seconds=router_seconds,
            retrieval_seconds=retrieval_seconds,
            rerank_seconds=rerank_seconds,
            retrieval_total_seconds=(
                retrieval_total_seconds
            ),
            generation_seconds=(
                generation_seconds
            ),
            safety_validation_seconds=(
                safety_validation_seconds
            ),
            total_seconds=total_seconds,

            # Keep this equal to total_seconds so old
            # analysis code continues working.
            latency_seconds=total_seconds,

            router_route=router_route,
            router_confidence=router_confidence,
            router_reason=router_reason,
            safety_validator_safe=True,
            safety_validator_violation_type="none",
            safety_validator_regenerate_as="none",
            safety_validator_reason=(
                safety_reason
                or "Blocked before generation."
            ),
            guardrail_type=guardrail_type,
        ).to_dict()

    def answer(
        self,
        query: str,
        retriever_name: str,
        system_variant: str,
        use_reranker: bool,
        candidate_k: int = K_CANDIDATES,
        final_k: int = N_RESOURCE_TO_RETURN,
        min_retrieval_score: float | None = None,
        use_router: bool = True,
        use_validator: bool = True,
        temperature: float = 0.2,
        max_new_tokens: int = 512,
    ) -> dict:
        start_total = perf_counter()

        # ------------------------------------------------------------
        # Routing phase
        # ------------------------------------------------------------

        router_seconds = 0.0

        if use_router:
            start_router = perf_counter()

            if self.safety_router.is_query_sensitive(query):
                router_seconds = (
                    perf_counter()
                    - start_router
                )

                return self._guardrail_output(
                    query=query,
                    answer=OUT_OF_SCOPE_RESPONSE,
                    guardrail_type="security_rule",
                    system_variant=system_variant,
                    use_reranker=use_reranker,
                    candidate_k=candidate_k,
                    final_k=final_k,
                    start_total=start_total,
                    router_route="security_or_prompt_injection",
                    router_confidence=1.0,
                    router_reason=(
                        "Matched deterministic security rule."
                    ),
                    safety_reason="Blocked before generation.",
                    router_seconds=router_seconds,
                )

            router_result = (
                self.safety_router
                .classify_query_intent(query)
            )

            router_seconds = (
                perf_counter()
                - start_router
            )

            route = router_result["route"]

            if route == "security_or_prompt_injection":
                return self._guardrail_output(
                    query=query,
                    answer=OUT_OF_SCOPE_RESPONSE,
                    guardrail_type=(
                        "security_or_prompt_injection"
                    ),
                    system_variant=system_variant,
                    use_reranker=use_reranker,
                    candidate_k=candidate_k,
                    final_k=final_k,
                    start_total=start_total,
                    router_route=route,
                    router_confidence=(
                        router_result.get("confidence")
                    ),
                    router_reason=(
                        router_result.get("reason")
                    ),
                    safety_reason=(
                        "Blocked by router before generation."
                    ),
                    router_seconds=router_seconds,
                )

        else:
            # No-router ablation:
            # treat every query as normal nutrition QA.
            router_result = {
                "route": "normal_nutrition_qa",
                "confidence": None,
                "reason": (
                    "Router disabled for component ablation; "
                    "query forced to normal_nutrition_qa."
                ),
            }

            route = "normal_nutrition_qa"
            router_seconds = 0.0

        query_mode = "medical" if route == "personal_medical_safety" else "normal"

        if retriever_name not in self.retrievers:
            raise KeyError(f"Unknown retriever_name={retriever_name}. Available: {list(self.retrievers)}")

        retrieval: RetrievalOutput = self.retrievers[retriever_name].retrieve(
            query=query,
            final_k=final_k,
            candidate_k=candidate_k,
            use_reranker=use_reranker,
            reranker_model=self.reranker_model,
        )

        # retrieval_total_seconds already includes
        # rerank_seconds in the current retriever.
        # Subtract it to obtain retrieval-only time.
        retrieval_seconds = max(
            0.0,
            float(
                retrieval
                .retrieval_total_seconds
                or 0.0
            )
            -
            float(
                retrieval
                .rerank_seconds
                or 0.0
            ),
        )

        if not retrieval.context_items:
            return self._guardrail_output(
                query=query,
                answer=MEDICAL_SAFE_RESPONSE if query_mode == "medical" else OUT_OF_SCOPE_RESPONSE,
                guardrail_type=f"{query_mode}_no_context",
                system_variant=system_variant,
                use_reranker=use_reranker,
                candidate_k=candidate_k,
                final_k=final_k,
                start_total=start_total,
                router_route=route,
                router_confidence=router_result.get("confidence"),
                router_reason=router_result.get("reason"),
                safety_reason="No context retrieved; used safe fallback.",
                router_seconds=router_seconds,
                retrieval_seconds=retrieval_seconds,
                rerank_seconds=(
                    retrieval.rerank_seconds
                ),
                retrieval_total_seconds=(
                    retrieval.retrieval_total_seconds
                ),
            )

        context_items = retrieval.context_items
        result = GenerationOutput(
            question=query,
            answer="",
            contexts=[item["sentence_chunk"] for item in context_items],
            pages=[item.get("page_number", "Unknown") for item in context_items],
            scores=_score_list(context_items, retrieval.retrieval_score_type),
            rerank_scores=[item.get("rerank_score") for item in context_items],
            retrieved_vector_scores=[item.get("vector_score") for item in context_items],
            retrieved_bm25_scores=[item.get("bm25_score") for item in context_items],
            retrieved_hybrid_rrf_scores=[item.get("rrf_score") for item in context_items],
            retrieval_sources=[item.get("retrieval_sources") for item in context_items],
            retrieval_score_type=retrieval.retrieval_score_type,
            retrieval_threshold_score=retrieval.retrieval_threshold_score,
            top_vector_score=retrieval.top_vector_score,
            top_bm25_score=retrieval.top_bm25_score,
            top_hybrid_rrf_score=retrieval.top_hybrid_rrf_score,
            top_rerank_score=retrieval.top_rerank_score,
            top_final_vector_score=retrieval.top_final_vector_score,
            max_final_vector_score=retrieval.max_final_vector_score,
            top_final_bm25_score=retrieval.top_final_bm25_score,
            max_final_bm25_score=retrieval.max_final_bm25_score,
            top_final_hybrid_rrf_score=retrieval.top_final_hybrid_rrf_score,
            max_final_hybrid_rrf_score=retrieval.max_final_hybrid_rrf_score,
            router_seconds=router_seconds,
            query_embedding_seconds=retrieval.query_embedding_seconds,
            vector_search_seconds=retrieval.vector_search_seconds,
            topk_seconds=retrieval.topk_seconds,
            retrieval_seconds=retrieval_seconds,
            rerank_seconds=retrieval.rerank_seconds,
            retrieval_total_seconds=retrieval.retrieval_total_seconds,
            system_variant=system_variant,
            use_reranker=use_reranker,
            candidate_k=candidate_k,
            final_k=final_k,
            guardrail_type=query_mode,
            router_route=route,
            router_confidence=router_result.get("confidence"),
            router_reason=router_result.get("reason"),
        )

        if (
            min_retrieval_score is not None
            and retrieval.retrieval_threshold_score is not None
            and retrieval.retrieval_threshold_score < min_retrieval_score
        ):
            result.answer = MEDICAL_SAFE_RESPONSE if query_mode == "medical" else OUT_OF_SCOPE_RESPONSE
            result.guardrail_type = "medical_low_retrieval_score" if query_mode == "medical" else "low_retrieval_score"
            result.safety_validator_safe = True
            result.safety_validator_violation_type = "none"
            result.safety_validator_regenerate_as = "none"
            result.safety_validator_reason = (
                f"{retrieval.retrieval_score_type} retrieval score below threshold; used safe fallback."
            )
            total_seconds = (
                perf_counter()
                - start_total
            )

            result.total_seconds = total_seconds
            result.latency_seconds = total_seconds

            return result.to_dict()

        prompt = build_rag_prompt(query=query, context_items=context_items, query_mode=query_mode)
        # ------------------------------------------------------------
        # Generation API only
        # ------------------------------------------------------------

        start_generation = perf_counter()

        completion = (
            self.client
            .chat.completions
            .create(
                model=self.generation_model,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=float(
                    temperature
                ),
                max_tokens=int(
                    max_new_tokens
                ),
                stream=False,
            )
        )

        answer = (
            completion
            .choices[0]
            .message
            .content
            .strip()
        )

        generation_seconds = (
            perf_counter()
            - start_generation
        )


        # ------------------------------------------------------------
        # Post-generation safety validation
        # ------------------------------------------------------------

        final_answer = answer

        if use_validator:
            start_safety_validation = perf_counter()

            safety_check = (
                self.safety_router
                .validate_answer_safety(
                    query=query,
                    answer=answer,
                    route=route,
                )
            )

            safety_validation_seconds = (
                perf_counter()
                - start_safety_validation
            )

            result.safety_validator_safe = (
                safety_check.get("safe", True)
            )

            result.safety_validator_violation_type = (
                safety_check.get(
                    "violation_type",
                    "none",
                )
            )

            result.safety_validator_regenerate_as = (
                safety_check.get(
                    "should_regenerate_as",
                    "none",
                )
            )

            result.safety_validator_reason = (
                safety_check.get("reason", "")
            )

            if not safety_check.get("safe", True):
                result.answer_before_safety_fallback = answer

                action = safety_check.get(
                    "should_regenerate_as",
                    "none",
                )

                if action == "medical_safe":
                    final_answer = MEDICAL_SAFE_RESPONSE
                    result.guardrail_type = (
                        "medical_after_validator"
                    )

                elif action == "refusal":
                    final_answer = OUT_OF_SCOPE_RESPONSE
                    result.guardrail_type = (
                        "refusal_after_validator"
                    )

                else:
                    if route == "personal_medical_safety":
                        final_answer = MEDICAL_SAFE_RESPONSE
                        result.guardrail_type = (
                            "medical_validator_fallback"
                        )
                    else:
                        final_answer = OUT_OF_SCOPE_RESPONSE
                        result.guardrail_type = (
                            "refusal_validator_fallback"
                        )

        else:
            # No-validator ablation:
            # preserve the generator's original answer.
            safety_validation_seconds = 0.0

            result.safety_validator_safe = None
            result.safety_validator_violation_type = None
            result.safety_validator_regenerate_as = None
            result.safety_validator_reason = (
                "Validator disabled for component ablation."
            )

        result.answer = final_answer

        result.generation_seconds = (
            generation_seconds
        )

        result.safety_validation_seconds = (
            safety_validation_seconds
        )

        total_seconds = (
            perf_counter()
            - start_total
        )

        result.total_seconds = total_seconds

        # Backward-compatible alias.
        result.latency_seconds = total_seconds

        return result.to_dict()
    def answer_stream(
        self,
        query: str,
        retriever_name: str,
        system_variant: str,
        use_reranker: bool,
        candidate_k: int = K_CANDIDATES,
        final_k: int = N_RESOURCE_TO_RETURN,
        min_retrieval_score: float | None = MIN_VECTOR_SCORE,
        temperature: float = 0.2,
        max_new_tokens: int = 512,
    ):
        start_total = perf_counter()
        # Measure the complete routing phase.
        start_router = perf_counter()

        if self.safety_router.is_query_sensitive(query):
            router_seconds = (
                perf_counter()
                - start_router
            )
            result = self._guardrail_output(
                query=query,
                answer=OUT_OF_SCOPE_RESPONSE,
                guardrail_type="security_rule",
                system_variant=system_variant,
                use_reranker=use_reranker,
                candidate_k=candidate_k,
                final_k=final_k,
                start_total=start_total,
                router_route="security_or_prompt_injection",
                router_confidence=1.0,
                router_reason="Matched deterministic security rule.",
                safety_reason="Blocked before generation.",
                router_seconds=router_seconds,
            )
            result["streaming"] = False
            yield result
            return

        router_result = self.safety_router.classify_query_intent(query)
        router_seconds = (
            perf_counter()
            - start_router
        )
        route = router_result["route"]

        if route == "security_or_prompt_injection":
            result = self._guardrail_output(
                query=query,
                answer=OUT_OF_SCOPE_RESPONSE,
                guardrail_type="security_or_prompt_injection",
                system_variant=system_variant,
                use_reranker=use_reranker,
                candidate_k=candidate_k,
                final_k=final_k,
                start_total=start_total,
                router_route=route,
                router_confidence=router_result.get("confidence"),
                router_reason=router_result.get("reason"),
                safety_reason="Blocked by router before generation.",
                router_seconds=router_seconds,
            )
            result["streaming"] = False
            yield result
            return

        query_mode = "medical" if route == "personal_medical_safety" else "normal"

        if retriever_name not in self.retrievers:
            raise KeyError(
                f"Unknown retriever_name={retriever_name}. "
                f"Available: {list(self.retrievers)}"
            )

        retrieval: RetrievalOutput = self.retrievers[retriever_name].retrieve(
            query=query,
            final_k=final_k,
            candidate_k=candidate_k,
            use_reranker=use_reranker,
            reranker_model=self.reranker_model,
        )
        # retrieval_total_seconds already includes
        # rerank_seconds in the current retriever.
        # Subtract it to obtain retrieval-only time.
        retrieval_seconds = max(
            0.0,
            float(
                retrieval
                .retrieval_total_seconds
                or 0.0
            )
            -
            float(
                retrieval
                .rerank_seconds
                or 0.0
            ),
        )

        if not retrieval.context_items:
            result = self._guardrail_output(
                query=query,
                answer=MEDICAL_SAFE_RESPONSE if query_mode == "medical" else OUT_OF_SCOPE_RESPONSE,
                guardrail_type=f"{query_mode}_no_context",
                system_variant=system_variant,
                use_reranker=use_reranker,
                candidate_k=candidate_k,
                final_k=final_k,
                start_total=start_total,
                router_route=route,
                router_confidence=router_result.get("confidence"),
                router_reason=router_result.get("reason"),
                safety_reason="No context retrieved; used safe fallback.",
                        router_seconds=router_seconds,
                retrieval_seconds=(
                    retrieval_seconds
                ),
                rerank_seconds=(
                    retrieval.rerank_seconds
                ),
                retrieval_total_seconds=(
                    retrieval
                    .retrieval_total_seconds
                ),
            )
            result["streaming"] = False
            yield result
            return

        context_items = retrieval.context_items

        result = GenerationOutput(
            question=query,
            answer="",
            contexts=[item["sentence_chunk"] for item in context_items],
            pages=[item.get("page_number", "Unknown") for item in context_items],
            scores=_score_list(context_items, retrieval.retrieval_score_type),
            rerank_scores=[item.get("rerank_score") for item in context_items],
            retrieved_vector_scores=[item.get("vector_score") for item in context_items],
            retrieved_bm25_scores=[item.get("bm25_score") for item in context_items],
            retrieved_hybrid_rrf_scores=[item.get("rrf_score") for item in context_items],
            retrieval_sources=[item.get("retrieval_sources") for item in context_items],
            retrieval_score_type=retrieval.retrieval_score_type,
            retrieval_threshold_score=retrieval.retrieval_threshold_score,
            top_vector_score=retrieval.top_vector_score,
            top_bm25_score=retrieval.top_bm25_score,
            top_hybrid_rrf_score=retrieval.top_hybrid_rrf_score,
            top_rerank_score=retrieval.top_rerank_score,
            top_final_vector_score=retrieval.top_final_vector_score,
            max_final_vector_score=retrieval.max_final_vector_score,
            top_final_bm25_score=retrieval.top_final_bm25_score,
            max_final_bm25_score=retrieval.max_final_bm25_score,
            top_final_hybrid_rrf_score=retrieval.top_final_hybrid_rrf_score,
            max_final_hybrid_rrf_score=retrieval.max_final_hybrid_rrf_score,
            router_seconds=router_seconds,
            query_embedding_seconds=retrieval.query_embedding_seconds,
            vector_search_seconds=retrieval.vector_search_seconds,
            topk_seconds=retrieval.topk_seconds,
            retrieval_seconds=retrieval_seconds,
            rerank_seconds=retrieval.rerank_seconds,
            retrieval_total_seconds=retrieval.retrieval_total_seconds,
            system_variant=system_variant,
            use_reranker=use_reranker,
            candidate_k=candidate_k,
            final_k=final_k,
            guardrail_type=query_mode,
            router_route=route,
            router_confidence=router_result.get("confidence"),
            router_reason=router_result.get("reason"),
        )

        if (
            min_retrieval_score is not None
            and retrieval.retrieval_threshold_score is not None
            and retrieval.retrieval_threshold_score < min_retrieval_score
        ):
            result.answer = MEDICAL_SAFE_RESPONSE if query_mode == "medical" else OUT_OF_SCOPE_RESPONSE
            result.guardrail_type = (
                "medical_low_retrieval_score"
                if query_mode == "medical"
                else "low_retrieval_score"
            )
            result.safety_validator_safe = True
            result.safety_validator_violation_type = "none"
            result.safety_validator_regenerate_as = "none"
            result.safety_validator_reason = (
                f"{retrieval.retrieval_score_type} retrieval score below threshold; "
                "used safe fallback."
            )
            total_seconds = (
                perf_counter()
                - start_total
            )

            result.total_seconds = total_seconds
            result.latency_seconds = total_seconds

            output = result.to_dict()
            output["streaming"] = False
            yield output
            return

        prompt = build_rag_prompt(
            query=query,
            context_items=context_items,
            query_mode=query_mode,
        )

                # ------------------------------------------------------------
        # Streamed answer generation
        # ------------------------------------------------------------

        start_generation = perf_counter()

        completion = (
            self.client
            .chat.completions
            .create(
                model=self.generation_model,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=float(
                    temperature
                ),
                max_tokens=int(
                    max_new_tokens
                ),
                stream=True,
            )
        )

        partial_answer = ""


        # ------------------------------------------------------------
        # Yield partial streamed outputs
        # ------------------------------------------------------------

        for chunk in completion:
            delta = ""

            if chunk.choices:
                delta = (
                    chunk
                    .choices[0]
                    .delta
                    .content
                    or ""
                )

            if not delta:
                continue

            partial_answer += delta

            # During streaming, this is generation time elapsed so far.
            elapsed_generation_seconds = (
                perf_counter()
                - start_generation
            )

            # During streaming, this is total pipeline time elapsed so far.
            elapsed_total_seconds = (
                perf_counter()
                - start_total
            )

            result.answer = partial_answer
            result.generation_seconds = (
                elapsed_generation_seconds
            )

            # Safety validation has not happened yet.
            result.safety_validation_seconds = 0.0

            result.total_seconds = (
                elapsed_total_seconds
            )

            # Backward-compatible alias.
            result.latency_seconds = (
                elapsed_total_seconds
            )

            output = result.to_dict()
            output["streaming"] = True

            yield output


        # ------------------------------------------------------------
        # Stop the generation timer immediately after streaming ends
        # ------------------------------------------------------------

        generation_seconds = (
            perf_counter()
            - start_generation
        )


        # ------------------------------------------------------------
        # Post-generation safety validation only
        # ------------------------------------------------------------

        start_safety_validation = (
            perf_counter()
        )

        safety_check = (
            self.safety_router
            .validate_answer_safety(
                query=query,
                answer=partial_answer,
                route=route,
            )
        )

        safety_validation_seconds = (
            perf_counter()
            - start_safety_validation
        )


        result.safety_validator_safe = (
            safety_check.get(
                "safe",
                True,
            )
        )

        result.safety_validator_violation_type = (
            safety_check.get(
                "violation_type",
                "none",
            )
        )

        result.safety_validator_regenerate_as = (
            safety_check.get(
                "should_regenerate_as",
                "none",
            )
        )

        result.safety_validator_reason = (
            safety_check.get(
                "reason",
                "",
            )
        )


        # ------------------------------------------------------------
        # Apply the safety fallback when necessary
        # ------------------------------------------------------------

        final_answer = partial_answer

        if not safety_check.get(
            "safe",
            True,
        ):
            result.answer_before_safety_fallback = (
                partial_answer
            )

            action = safety_check.get(
                "should_regenerate_as",
                "none",
            )

            if action == "medical_safe":
                final_answer = (
                    MEDICAL_SAFE_RESPONSE
                )

                result.guardrail_type = (
                    "medical_after_validator"
                )

            elif action == "refusal":
                final_answer = (
                    OUT_OF_SCOPE_RESPONSE
                )

                result.guardrail_type = (
                    "refusal_after_validator"
                )

            else:
                final_answer = (
                    MEDICAL_SAFE_RESPONSE
                    if route
                    == "personal_medical_safety"
                    else OUT_OF_SCOPE_RESPONSE
                )

                result.guardrail_type = (
                    "medical_validator_fallback"
                    if route
                    == "personal_medical_safety"
                    else "refusal_validator_fallback"
                )


        # ------------------------------------------------------------
        # Save the final timing values
        # ------------------------------------------------------------

        result.answer = final_answer

        # Generation API and token streaming only.
        result.generation_seconds = (
            generation_seconds
        )

        # Safety-validator API only.
        result.safety_validation_seconds = (
            safety_validation_seconds
        )

        # Complete wall-clock pipeline time.
        total_seconds = (
            perf_counter()
            - start_total
        )

        result.total_seconds = total_seconds

        # Keep this for compatibility with old notebooks.
        result.latency_seconds = total_seconds


        # ------------------------------------------------------------
        # Yield the final validated output
        # ------------------------------------------------------------

        output = result.to_dict()
        output["streaming"] = False

        yield output

class LLMOnlyPipeline:
    def __init__(
        self,
        client,
        generation_model: str = GENERATION_MODEL,
        safety_router: SafetyRouter | None = None,
    ):
        self.client = client
        self.generation_model = generation_model
        self.safety_router = safety_router or SafetyRouter(client)

    def _guardrail_output(
        self,
        query: str,
        answer: str,
        guardrail_type: str,
        start_total: float,
        router_result: dict,
        safety_reason: str,
        router_seconds: float,
        system_variant: str,
    ) -> dict:
        total_seconds = (
            perf_counter()
            - start_total
        )

        return GenerationOutput(
            question=query,
            answer=answer,
            system_variant=system_variant,
            use_reranker=False,
            candidate_k=None,
            final_k=None,
            router_seconds=router_seconds,
            generation_seconds=0.0,
            safety_validation_seconds=0.0,
            total_seconds=total_seconds,
            latency_seconds=total_seconds,
            guardrail_type=guardrail_type,
            router_route=router_result.get("route"),
            router_confidence=router_result.get(
                "confidence"
            ),
            router_reason=router_result.get("reason"),
            safety_validator_safe=True,
            safety_validator_violation_type="none",
            safety_validator_regenerate_as="none",
            safety_validator_reason=safety_reason,
        ).to_dict()

    def answer(
        self,
        query: str,
        system_variant: str = "llm_only",
        use_router: bool = True,
        use_validator: bool = True,
        temperature: float = 0.2,
        max_new_tokens: int = 512,
    ) -> dict:
        start_total = perf_counter()

        # ========================================================
        # Optional routing pathway
        # ========================================================

        if use_router:
            start_router = perf_counter()

            if self.safety_router.is_query_sensitive(query):
                router_seconds = (
                    perf_counter()
                    - start_router
                )

                return self._guardrail_output(
                    query=query,
                    answer=OUT_OF_SCOPE_RESPONSE,
                    guardrail_type="security_rule",
                    start_total=start_total,
                    router_result={
                        "route": (
                            "security_or_prompt_injection"
                        ),
                        "confidence": 1.0,
                        "reason": (
                            "Matched deterministic "
                            "security rule."
                        ),
                    },
                    safety_reason=(
                        "Blocked before generation."
                    ),
                    router_seconds=router_seconds,
                    system_variant=system_variant,
                )

            router_result = (
                self.safety_router
                .classify_query_intent(query)
            )

            router_seconds = (
                perf_counter()
                - start_router
            )

            route = router_result["route"]

            if (
                route
                == "security_or_prompt_injection"
            ):
                return self._guardrail_output(
                    query=query,
                    answer=(
                        LLM_ONLY_OUT_OF_SCOPE_RESPONSE
                    ),
                    guardrail_type=route,
                    start_total=start_total,
                    router_result=router_result,
                    safety_reason=(
                        "Blocked by router before "
                        "generation."
                    ),
                    router_seconds=router_seconds,
                    system_variant=system_variant,
                )

        else:
            # Router-disabled LLM-only ablation:
            # all queries use the normal LLM-only prompt.
            router_seconds = 0.0

            router_result = {
                "route": "normal_nutrition_qa",
                "confidence": None,
                "reason": (
                    "Router disabled for LLM-only "
                    "component ablation."
                ),
            }

            route = "normal_nutrition_qa"

        # Without routing, the medical-specific prompt is
        # intentionally not selected.
        query_mode = (
            "medical"
            if route == "personal_medical_safety"
            else "normal"
        )

        user_prompt = build_llm_only_prompt(
            query=query,
            query_mode=query_mode,
        )

        # ========================================================
        # Generation
        # ========================================================

        start_generation = perf_counter()

        completion = (
            self.client
            .chat.completions
            .create(
                model=self.generation_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            LLM_ONLY_SYSTEM_PROMPT
                        ),
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=float(temperature),
                max_tokens=int(max_new_tokens),
                stream=False,
            )
        )

        answer = (
            completion
            .choices[0]
            .message
            .content
            .strip()
        )

        generation_seconds = (
            perf_counter()
            - start_generation
        )

        # ========================================================
        # Optional post-generation validation
        # ========================================================

        final_answer = answer
        answer_before_safety_fallback = None
        guardrail_type = query_mode

        if use_validator:
            start_safety_validation = (
                perf_counter()
            )

            safety_check = (
                self.safety_router
                .validate_answer_safety(
                    query=query,
                    answer=answer,
                    route=route,
                )
            )

            safety_validation_seconds = (
                perf_counter()
                - start_safety_validation
            )

            if not safety_check.get("safe", True):
                answer_before_safety_fallback = answer

                action = safety_check.get(
                    "should_regenerate_as",
                    "none",
                )

                if action == "medical_safe":
                    final_answer = (
                        MEDICAL_SAFE_RESPONSE
                    )
                    guardrail_type = (
                        "medical_after_validator"
                    )

                elif action == "refusal":
                    final_answer = (
                        OUT_OF_SCOPE_RESPONSE
                    )
                    guardrail_type = (
                        "refusal_after_validator"
                    )

                else:
                    if (
                        route
                        == "personal_medical_safety"
                    ):
                        final_answer = (
                            MEDICAL_SAFE_RESPONSE
                        )
                        guardrail_type = (
                            "medical_validator_fallback"
                        )
                    else:
                        final_answer = (
                            OUT_OF_SCOPE_RESPONSE
                        )
                        guardrail_type = (
                            "refusal_validator_fallback"
                        )

            validator_safe = safety_check.get(
                "safe",
                True,
            )

            validator_violation = (
                safety_check.get(
                    "violation_type",
                    "none",
                )
            )

            validator_action = safety_check.get(
                "should_regenerate_as",
                "none",
            )

            validator_reason = safety_check.get(
                "reason",
                "",
            )

        else:
            # Validator-disabled LLM-only ablation:
            # return the generated answer unchanged.
            safety_validation_seconds = 0.0

            validator_safe = None
            validator_violation = None
            validator_action = None

            validator_reason = (
                "Post-generation validator disabled "
                "for LLM-only component ablation."
            )

        total_seconds = (
            perf_counter()
            - start_total
        )

        return GenerationOutput(
            question=query,
            answer=final_answer,
            system_variant=system_variant,
            use_reranker=False,
            candidate_k=None,
            final_k=None,
            router_seconds=router_seconds,
            generation_seconds=generation_seconds,
            safety_validation_seconds=(
                safety_validation_seconds
            ),
            total_seconds=total_seconds,
            latency_seconds=total_seconds,
            guardrail_type=guardrail_type,
            router_route=route,
            router_confidence=(
                router_result.get("confidence")
            ),
            router_reason=(
                router_result.get("reason")
            ),
            safety_validator_safe=validator_safe,
            safety_validator_violation_type=(
                validator_violation
            ),
            safety_validator_regenerate_as=(
                validator_action
            ),
            safety_validator_reason=(
                validator_reason
            ),
            answer_before_safety_fallback=(
                answer_before_safety_fallback
            ),
        ).to_dict()