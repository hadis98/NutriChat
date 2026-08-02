from __future__ import annotations

from html import escape

from nutrichat.app.icons import SVG_ICONS


def _safe(value) -> str:
    return escape(str(value)) if value is not None else "—"


def _fmt(value, digits: int = 2) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def _system_label(system_variant: str | None) -> str:
    labels = {
        "dense_rag_no_reranker": "Dense RAG, no reranker",
        "dense_rag_with_reranker": "Dense RAG + reranker",
        "bm25_rag_no_reranker": "BM25 RAG, no reranker",
        "bm25_rag_with_reranker": "BM25 RAG + reranker",
        "hybrid_dense_bm25_rrf_no_reranker": "Hybrid RRF, no reranker",
        "hybrid_dense_bm25_rrf_reranker": "Hybrid RRF + reranker",
    }
    return labels.get(system_variant or "", system_variant or "—")


def _route_label(route: str | None) -> str:
    labels = {
        "normal_nutrition_qa": "Normal nutrition QA",
        "personal_medical_safety": "Medical safety",
        "out_of_scope": "Out of scope",
        "security_or_prompt_injection": "Prompt injection / security",
    }
    return labels.get(route or "", route or "—")


def _score_label(score_type: str | None, score) -> str:
    try:
        score = float(score)
    except Exception:
        return "Retrieved evidence"

    if score_type == "vector":
        if score >= 0.70:
            return "Strong semantic match"
        if score >= 0.55:
            return "Moderate semantic match"
        return "Weak semantic match"

    if score_type == "bm25":
        if score >= 8:
            return "Strong keyword match"
        if score >= 4:
            return "Moderate keyword match"
        return "Weak keyword match"

    if score_type == "hybrid_rrf":
        if score >= 0.04:
            return "Strong hybrid match"
        if score >= 0.02:
            return "Moderate hybrid match"
        return "Weak hybrid match"

    return "Retrieved evidence"


def _mini_icon(name: str, class_name: str = "") -> str:
    classes = f"result-icon {class_name}".strip()
    return f'<span class="{classes}" aria-hidden="true">{SVG_ICONS[name]}</span>'


def _empty_panel(message: str) -> str:
    return f"""
        <div class="empty-panel">
          {_safe(message)}
        </div>
        """


def _list_value(values: list, index: int, default=None):
    return values[index] if index < len(values) else default


def _source_snippet(context) -> str:
    snippet = str(context).replace("\n", " ").strip()
    if len(snippet) > 850:
        return snippet[:850] + "..."
    return snippet


def _render_score_grid(
    score,
    vector_score,
    bm25_score,
    rrf_score,
    rerank_score,
) -> str:
    return f"""
            <div class="score-grid">
              <div><span>Displayed</span><strong>{_fmt(score, 4)}</strong></div>
              <div><span>Vector</span><strong>{_fmt(vector_score, 4)}</strong></div>
              <div><span>BM25</span><strong>{_fmt(bm25_score, 4)}</strong></div>
              <div><span>RRF</span><strong>{_fmt(rrf_score, 4)}</strong></div>
              <div><span>Rerank</span><strong>{_fmt(rerank_score, 4)}</strong></div>
            </div>
    """


def _render_source_card(
    index: int,
    context,
    page,
    score,
    score_type: str | None,
    vector_score,
    bm25_score,
    rrf_score,
    rerank_score,
) -> str:
    label = _score_label(score_type, score)
    snippet = _source_snippet(context)

    return f"""
        <details class="source-card" open>
          <summary>
            <span class="source-title">Source {index}</span>
            <span class="page-badge">Page {_safe(page)}</span>
          </summary>

          <div class="source-card-body">
            <div class="evidence-row">
              <span class="evidence-pill">{_safe(label)}</span>
              <span class="score-pill">{_safe(score_type)} score: {_fmt(score, 4)}</span>
            </div>

            {_render_score_grid(score, vector_score, bm25_score, rrf_score, rerank_score)}

            <blockquote class="source-snippet">
              {_safe(snippet)}
            </blockquote>
          </div>
        </details>
        """


def _render_quick_row(
    icon: str,
    label: str,
    value: str,
    icon_class: str = "blue",
    value_class: str = "",
) -> str:
    class_attr = f' class="{value_class}"' if value_class else ""
    return f"""
      <div class="quick-row">
        {_mini_icon(icon, icon_class)}<span class="quick-row-icon-label">{_safe(label)}</span>
        <strong{class_attr}>{value}</strong>
      </div>
    """


def _render_diagnostic_card(title: str, icon: str, rows: list[tuple[str, str]]) -> str:
    table_rows = "\n".join(
        f"          <tr><td>{_safe(label)}</td><td>{value}</td></tr>"
        for label, value in rows
    )
    return f"""
      <div class="diagnostic-card">
        <h3>{_mini_icon(icon, "blue")}{_safe(title)}</h3>
        <table>
          <tr><th>Stage</th><th>Time / value</th></tr>
{table_rows}
        </table>
      </div>
    """


def _about_answer_message(route: str | None) -> str:
    if route == "personal_medical_safety":
        return (
            "This response follows a medical-safety route. It may provide general "
            "educational information, but it does not diagnose, treat, or recommend dosage."
        )

    if route in {"out_of_scope", "security_or_prompt_injection"}:
        return (
            "This response was not answered with textbook sources because the question "
            "was outside the supported nutrition-textbook scope or triggered a safety rule."
        )

    return (
        "This answer was generated using retrieved textbook context. "
        "It does not include personal medical advice."
    )


def format_sources(result: dict) -> str:
    contexts = result.get("contexts") or []
    pages = result.get("pages") or []
    scores = result.get("scores") or []
    rerank_scores = result.get("rerank_scores") or []
    vector_scores = result.get("retrieved_vector_scores") or []
    bm25_scores = result.get("retrieved_bm25_scores") or []
    rrf_scores = result.get("retrieved_hybrid_rrf_scores") or []

    if not contexts:
        return _empty_panel("No textbook sources are shown for this response.")

    score_type = result.get("retrieval_score_type")

    html = """
    <div class="sources-panel">
      <div class="panel-title-row">
        <div>
          <h2>Retrieved Sources</h2>
          <p>Textbook passages used as evidence for this answer.</p>
        </div>
      </div>
    """

    for i, context in enumerate(contexts, start=1):
        item_index = i - 1
        html += _render_source_card(
            index=i,
            context=context,
            page=_list_value(pages, item_index, "Unknown"),
            score=_list_value(scores, item_index),
            score_type=score_type,
            vector_score=_list_value(vector_scores, item_index),
            bm25_score=_list_value(bm25_scores, item_index),
            rrf_score=_list_value(rrf_scores, item_index),
            rerank_score=_list_value(rerank_scores, item_index),
        )

    html += "</div>"
    return html


def format_quick_info(result: dict | None) -> str:
    if not result:
        return """
        <div class="side-card quick-info-card">
          <h3><span class="quick-info-dot">i</span> <span>Quick Info</span></h3>
          <p class="muted">Ask a question to see system details.</p>
        </div>
        """

    contexts = result.get("contexts") or []
    rows = [
        (
            "server",
            "System",
            _safe(_system_label(result.get("system_variant"))),
            "green",
            "tag green",
        ),
        (
            "shield",
            "Safety route",
            _safe(_route_label(result.get("router_route"))),
            "green",
            "tag green",
        ),
        (
            "expand_arrows",
            "Retrieval score type",
            _safe(result.get("retrieval_score_type")),
            "blue",
            "tag blue",
        ),
        ("cube", "Retrieved chunks", str(len(contexts)), "blue", ""),
        (
            "clock",
            "Retrieval time",
            f"{_fmt(result.get('retrieval_total_seconds'), 2)}s",
            "blue",
            "",
        ),
        (
            "zap",
            "Generation time",
            f"{_fmt(result.get('generation_seconds'), 2)}s",
            "blue",
            "",
        ),
        (
            "stopwatch",
            "Total latency",
            f"{_fmt(result.get('latency_seconds'), 2)}s",
            "blue",
            "",
        ),
    ]
    quick_rows = "".join(
        _render_quick_row(
            icon=icon,
            label=label,
            value=value,
            icon_class=icon_class,
            value_class=value_class,
        )
        for icon, label, value, icon_class, value_class in rows
    )

    return f"""
    <div class="side-card quick-info-card">
      <h3><span class="quick-info-dot">i</span> <span>Quick Info</span></h3>
{quick_rows}
    </div>
    """


def format_about_answer(result: dict | None) -> str:
    if not result:
        return """
        <div class="side-card about-answer-card">
          <h3><span class="result-icon blue" aria-hidden="true">""" + SVG_ICONS["info"] + """</span>About this answer</h3>
          <p>
            NutriChat answers questions using retrieved textbook context.
            It is for educational use only and does not provide personal medical advice.
          </p>
        </div>
        """

    message = _about_answer_message(result.get("router_route"))

    return f"""
    <div class="side-card about-answer-card">
      <h3>{_mini_icon("info", "blue")}About this answer</h3>
      <p>{_safe(message)}</p>
    </div>
    """


def format_diagnostics(result: dict) -> str:
    if not result:
        return _empty_panel("Diagnostics will appear after you ask a question.")

    retrieval_rows = [
        ("Query embedding", f"{_fmt(result.get('query_embedding_seconds'), 4)}s"),
        ("Vector search", f"{_fmt(result.get('vector_search_seconds'), 4)}s"),
        ("Top-k selection", f"{_fmt(result.get('topk_seconds'), 4)}s"),
        ("Reranking", f"{_fmt(result.get('rerank_seconds'), 4)}s"),
        ("Total retrieval", f"{_fmt(result.get('retrieval_total_seconds'), 4)}s"),
    ]
    generation_rows = [
        ("Generation time", f"{_fmt(result.get('generation_seconds'), 4)}s"),
        ("Total latency", f"{_fmt(result.get('latency_seconds'), 4)}s"),
        ("Candidate k", _safe(result.get("candidate_k"))),
        ("Final k", _safe(result.get("final_k"))),
        ("Used reranker", _safe(result.get("use_reranker"))),
    ]

    return f"""
    <div class="diagnostics-panel">
      <h2>Diagnostics</h2>
{_render_diagnostic_card("Retrieval", "cube", retrieval_rows)}
{_render_diagnostic_card("Generation", "zap", generation_rows)}
    </div>
    """
