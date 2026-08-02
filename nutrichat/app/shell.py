import base64
from functools import lru_cache
from html import escape
from pathlib import Path
from urllib.parse import quote

from nutrichat.config import (
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_NEW_TOKENS,
    K_CANDIDATES,
    N_RESOURCE_TO_RETURN,
)
from nutrichat.app.examples import EXAMPLE_GROUPS
from nutrichat.app.icons import SVG_ICONS, svg_icon
from nutrichat.app.options import (
    DEFAULT_SYSTEM_CHOICE,
    SYSTEM_OPTIONS_FOR_UI,
)


ASSETS_DIR = Path(__file__).resolve().parent / "assets"
RESEARCH_DIAGRAM_PATH = ASSETS_DIR / "images" / "nutrichat-diagram.png"
RESEARCH_ASSETS_DIR = Path(__file__).resolve().parents[2] / "research_assets"
EVAL_DATASET_RELATIVE_PATH = "research_assets/test_dataset_300.json"
EVAL_DATASET_URL = f"/gradio_api/file={quote(EVAL_DATASET_RELATIVE_PATH, safe='/')}"
RESULTS_ZIP_PATH = RESEARCH_ASSETS_DIR / "judge_results.zip"
RESULTS_ZIP_RELATIVE_PATH = "research_assets/judge_results.zip"
RESULTS_ZIP_URL = f"/gradio_api/file={quote(RESULTS_ZIP_RELATIVE_PATH, safe='/')}"
PAPER_RELATIVE_PATH = "research_assets/Nutrichat_Paper.pdf"
PAPER_URL = f"/gradio_api/file={quote(PAPER_RELATIVE_PATH, safe='/')}"


@lru_cache(maxsize=1)
def _research_diagram_src() -> str:
    if not RESEARCH_DIAGRAM_PATH.exists():
        return ""

    encoded = base64.b64encode(RESEARCH_DIAGRAM_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _mode_menu_html() -> str:
    buttons = []
    for label, value in SYSTEM_OPTIONS_FOR_UI:
        selected = "true" if value == DEFAULT_SYSTEM_CHOICE else "false"
        active = " active" if value == DEFAULT_SYSTEM_CHOICE else ""
        buttons.append(
            f'''
            <button type="button" role="option" aria-selected="{selected}" class="nc-mode-option{active}"
                    data-label="{escape(label)}" data-value="{escape(value)}">
              {escape(label)}
            </button>
            '''
        )
    return "\n".join(buttons)


def _advanced_mode_options_html() -> str:
    options = [
        ("Dense", "Dense RAG, no reranker"),
        ("Dense + reranker", "Dense RAG + reranker"),
        ("BM25", "BM25 RAG, no reranker"),
        ("BM25 + reranker", "BM25 RAG + reranker"),
        ("Hybrid RRF", "Hybrid RRF, no reranker"),
        ("Hybrid RRF + reranker", "Hybrid RRF + reranker"),
    ]
    buttons = []
    select_options = []
    for label, value in options:
        selected = value == DEFAULT_SYSTEM_CHOICE
        select_options.append(
            f'<option value="{escape(value)}"{" selected" if selected else ""}>{escape(label)}</option>'
        )
        buttons.append(
            f'''
            <button type="button" role="option" aria-selected="{"true" if selected else "false"}"
                    class="nc-advanced-mode-option{" active" if selected else ""}"
                    data-label="{escape(label)}" data-value="{escape(value)}">
              <span>{escape(label)}</span>
            </button>
            '''
        )

    return "\n".join(select_options), "\n".join(buttons)


def _example_grid_html(
    category: str,
    questions: list[tuple[str, str]],
    hidden: bool = False,
) -> str:
    cards = []
    for question, icon in questions:
        cards.append(
            f'''
            <button type="button" class="nc-example-card" data-question="{escape(question)}">
              <span class="nc-example-icon nc-icon-{escape(icon)}" aria-hidden="true">{SVG_ICONS[icon]}</span>
              <span class="nc-example-text">{escape(question)}</span>
              <span class="nc-example-arrow" aria-hidden="true">›</span>
            </button>
            '''
        )
    hidden_attr = " hidden" if hidden else ""
    return f'<div class="nc-example-grid" data-panel="{escape(category)}"{hidden_attr}>{"".join(cards)}</div>'


BENCHMARK_ROWS = [
    ("Hybrid RRF + reranker", "92.00%", "4.71", "94.50%", "0.88", "20.92s", 92.0),
    ("Hybrid RRF, no reranker", "90.33%", "4.65", "92.50%", "0.80", "15.06s", 90.33),
    ("Dense RAG + reranker", "89.67%", "4.63", "92.50%", "0.87", "16.01s", 89.67),
    ("Dense RAG, no reranker", "89.33%", "4.60", "91.00%", "0.82", "13.94s", 89.33),
    ("BM25, no reranker", "89.33%", "4.56", "81.50%", "0.74", "16.63s", 89.33),
    ("BM25 + reranker", "89.00%", "4.58", "89.50%", "0.83", "13.62s", 89.0),
    ("LLM-only", "84.00%", "4.45", "--", "--", "32.08s", 84.0),
]


def _top_nav_html() -> str:
    tabs = [
        ("ask", "chat", "Ask NutriChat", "Ask", True),
        ("benchmark", "bar_chart", "Benchmark Dashboard", "Dashboard", False),
        ("research", "flask", "About the Research", "Research", False),
    ]
    buttons = []
    for panel, icon, label, mobile_label, active in tabs:
        buttons.append(
            f'''
            <button type="button" class="nc-app-tab{" active" if active else ""}"
                    data-app-tab="{escape(panel)}" aria-selected="{"true" if active else "false"}">
              <span aria-hidden="true">{SVG_ICONS[icon]}</span>
              <strong class="nc-app-tab-label-full">{escape(label)}</strong>
              <strong class="nc-app-tab-label-mobile">{escape(mobile_label)}</strong>
            </button>
            '''
        )
    return f'<nav class="nc-app-tabs" aria-label="NutriChat sections">{"".join(buttons)}</nav>'


def _metric_card_html(
    icon: str,
    tone: str,
    label: str,
    value: str,
    caption: str,
) -> str:
    return f"""
      <article class="nc-bench-metric">
        <div class="nc-bench-metric-label">
          <span class="nc-bench-icon nc-bench-{escape(tone)}" aria-hidden="true">{SVG_ICONS[icon]}</span>
          <span>{escape(label)}</span>
        </div>
        <span class='nc-bench-metric-value'>{escape(value)}</span>
        <small>{escape(caption)}</small>
      </article>
    """


def _pass_rate_html() -> str:
    rows = []
    for system, pass_rate, *_rest, progress in BENCHMARK_ROWS:
        rows.append(
            f"""
            <div class="nc-pass-row">
              <span class="nc-pass-row-name">{escape(system)}</span>
              <span class="nc-pass-track" aria-hidden="true">
                <span style="width: {progress:.2f}%"></span>
              </span>
              <span class='nc-pass-row-number'>{escape(pass_rate)}</span>
            </div>
            """
        )
    return "\n".join(rows)


def _error_card_html(icon: str, tone: str, title: str, code: str, body: str) -> str:
    return f"""
      <article class="nc-error-card">
        <span class="nc-error-icon nc-error-{escape(tone)}" aria-hidden="true">{SVG_ICONS[icon]}</span>
        <div>
          <strong>{escape(title)}</strong>
          <p>{escape(body)}</p>
        </div>
        <b>{escape(code)}</b>
      </article>
    """


def _benchmark_table_html() -> str:
    rows = []
    for system, pass_rate, mean_score, page_hit, mrr, latency, _progress in BENCHMARK_ROWS:
        rows.append(
            f"""
            <tr>
              <th scope="row">{escape(system)}</th>
              <td>{escape(pass_rate)}</td>
              <td>{escape(mean_score)}</td>
              <td>{escape(page_hit)}</td>
              <td>{escape(mrr)}</td>
              <td>{escape(latency)}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def _benchmark_dashboard_html() -> str:
    return f"""
      <section class="nc-tab-panel nc-benchmark-panel" data-tab-panel="benchmark" hidden>
        <div class="nc-dashboard-hero">
          <div>            
            <h1>Benchmark Dashboard</h1>
            <p>A static, reproducible view of the paper results using precomputed CSV/JSON artifacts. No live judge calls are made.</p>
          </div>
          <div class="nc-bench-metrics">
            {_metric_card_html("trend_up", "green", "Overall pass rate", "92.0%", "Hybrid RRF + reranker")}
            {_metric_card_html("target", "blue", "Page hit@3", "94.5%", "Expected page in top 3")}
            {_metric_card_html("chart_line", "purple", "MRR", "0.88", "Expected pages ranked near the top")}
            {_metric_card_html("shield", "blue", "Held-out benchmark", "300", "200 answerable + 100 safety/scope")}
            {_metric_card_html("clock", "green", "Gain over LLM-only", "+8.0 pp", "92.0% vs. 84.0%")}
          </div>
        </div>

        <div class="nc-benchmark-grid">
          <section class="nc-dashboard-card nc-pass-card">
            <div class="nc-section-heading">
              <div>
                <h2>Pass rate by system</h2>
              </div>
              <span>300 questions</span>
            </div>
            <div class="nc-pass-list">
              {_pass_rate_html()}
            </div>
          </section>
        </div>

        <section class="nc-dashboard-card nc-results-table-card">
          <h2>Benchmark results table</h2>
          <p>Detailed comparison of retrieval systems and reranking configurations.</p>
          <div class="nc-results-table-wrap">
            <table class="nc-results-table">
              <thead>
                <tr>
                  <th>System</th>
                  <th>Pass rate</th>
                  <th>Mean score</th>
                  <th>Page hit@3</th>
                  <th>MRR</th>
                  <th>Median latency</th>
                </tr>
              </thead>
              <tbody>
                {_benchmark_table_html()}
              </tbody>
            </table>
          </div>
          <p class="nc-artifact-note"><span aria-hidden="true">{SVG_ICONS["info"]}</span> Version 1 · July 2026</p>
        </section>
      </section>
    """


def _about_research_html() -> str:
    diagram_src = escape(_research_diagram_src(), quote=True)

    return f"""
      <section class="nc-tab-panel nc-research-panel" data-tab-panel="research" hidden>
        <section class="nc-research-card">
          <header class="nc-research-intro">
            <h1>About the Research</h1>
            <p>
              NutriChat is a safety-aware Retrieval-Augmented Generation (RAG) system for answering
              nutrition questions using a textbook as the single trusted source.
            </p>
            <p>
              This page describes the architecture, data, evaluation protocol, and research
              contributions behind the system.
            </p>
          </header>

          <section class="nc-featured-paper" aria-labelledby="nc-paper-title">
            <span class="nc-featured-paper-icon" aria-hidden="true">{SVG_ICONS["file_text"]}</span>
            <div class="nc-featured-paper-content">
              <div class="nc-paper-kicker">
                <span aria-hidden="true">&#9733;</span>
                Featured Research Paper
              </div>
              <h1 class="nc-paper-title" id="nc-paper-title">
                NutriChat: Evaluating Safety-Aware Retrieval-Augmented<br class="nc-paper-title-break" />
                Generation for Nutrition Textbook Question Answering
              </h1>
              <p>Full paper with benchmark design, methodology, experiments, results, and error analysis.</p>
              <div class="nc-paper-actions">
                <a class="nc-paper-primary-action" href="{PAPER_URL}" target="_blank" rel="noreferrer">
                  <span aria-hidden="true">{SVG_ICONS["file_text"]}</span>
                  View Paper PDF
                </a>
                <button class="nc-paper-copy-action" type="button" data-copy-citation>
                  <span aria-hidden="true">{SVG_ICONS["copy"]}</span>
                  <span data-copy-label aria-live="polite">Copy Citation</span>
                </button>
              </div>
            </div>
            <div class="nc-paper-badges" aria-label="Paper formats">
              <span class="nc-paper-badge nc-paper-badge-preprint">
                <span aria-hidden="true">{SVG_ICONS["flask"]}</span> Preprint
              </span>
            </div>
          </section>

          <section class="nc-research-section nc-architecture-section">
            <div class="nc-research-section-heading">
              <span class="nc-section-number">1</span>
              <div>
                <h2>System Architecture</h2>
                <p>Overview of the end-to-end pipeline.</p>
              </div>
            </div>
            <figure class="nc-architecture-figure">
              <img src="{diagram_src}" alt="NutriChat system architecture diagram" />
            </figure>
          </section>

          <section class="nc-research-section">
            <div class="nc-research-section-heading">
              <span class="nc-section-number">2</span>
              <div>
                <h2>Data &amp; Resources</h2>
                <p>All key artifacts used in this research.</p>
              </div>
            </div>
            <div class="nc-resource-grid">
              <article class="nc-resource-card nc-resource-green">
                <span class="nc-resource-icon" aria-hidden="true">{SVG_ICONS["file_text"]}</span>
                <div>
                  <h3>Nutrition Textbook (Source)</h3>
                  <p>The single trusted source used for all answers. Page-preserving PDF with metadata.</p>
                </div>
                <a href="https://louis.pressbooks.pub/nutrition/open/download?type=pdf" target="_blank" rel="noreferrer">
                  <span aria-hidden="true">{SVG_ICONS["file_text"]}</span>
                  View / Download PDF
                </a>
              </article>
              <article class="nc-resource-card nc-resource-blue">
                <span class="nc-resource-icon" aria-hidden="true">{SVG_ICONS["server"]}</span>
                <div>
                  <h3>Evaluation Dataset (NutriChat-Bench)</h3>
                  <p>Our benchmark with labeled questions: answerable, unsupported, prompt injection, medical-safe, out-of-scope.</p>
                </div>
                <a href="{EVAL_DATASET_URL}" download="test_dataset_300.json">
                  <span aria-hidden="true">{SVG_ICONS["bar_chart"]}</span>
                  Download Dataset JSON
                </a>
              </article>
              <article class="nc-resource-card nc-resource-purple">
                <span class="nc-resource-icon" aria-hidden="true">{SVG_ICONS["file_text"]}</span>
                <div>
                  <h3>Results (CSV)</h3>
                  <p>Precomputed results for all systems and metrics used in the paper and dashboard.</p>
                </div>
                <a href="{RESULTS_ZIP_URL}" download="judge_results.zip">
                  <span aria-hidden="true">{SVG_ICONS["file_text"]}</span>
                  Download Results ZIP
                </a>
              </article>
              <article class="nc-resource-card nc-resource-orange">
                <span class="nc-resource-icon" aria-hidden="true">{SVG_ICONS["cube"]}</span>
                <div>
                  <h3>GitHub Repository</h3>
                  <p>Source code, configs, indexing scripts, and evaluation notebooks.</p>
                </div>
                <a href="https://github.com/" target="_blank" rel="noreferrer">
                  <span aria-hidden="true">{SVG_ICONS["github"]}</span>
                  Visit GitHub Repo
                </a>
              </article>
            </div>
          </section>

          <div class="nc-research-two-col">
            <section class="nc-research-section nc-research-subcard">
              <div class="nc-subcard-heading">
                <span class="nc-subcard-icon nc-subcard-blue" aria-hidden="true">{SVG_ICONS["target"]}</span>
                <h2>Research Contributions</h2>
              </div>
              <ul class="nc-contribution-list">
                <li>NutriChat-Bench: a safety-aware benchmark for nutrition textbook QA.</li>
                <li>Safety-aware RAG pipeline with routing for unsupported, unsafe, and out-of-scope questions.</li>
                <li>Comprehensive evaluation of retrieval strategies (dense, BM25, hybrid RRF) with and without reranking.</li>
                <li>Analysis of safety behavior, refusal correctness, and failure modes.</li>
                <li>Fully reproducible research artifact with open data, code, and demo.</li>
              </ul>
            </section>

            <section class="nc-research-section nc-research-subcard">
              <div class="nc-subcard-heading">
                <span class="nc-subcard-icon nc-subcard-blue" aria-hidden="true">{SVG_ICONS["bar_chart"]}</span>
                <div>
                  <h2>Evaluation at a Glance</h2>
                  <p>Key results across all evaluated systems.</p>
                </div>
              </div>
              <div class="nc-glance-grid">
                <article>
                  <span>Overall pass rate</span>
                  <strong>92.0%</strong>
                  <small>Hybrid RRF + RR</small>
                </article>
                <article>
                  <span>Page hit@3</span>
                  <strong>94.5%</strong>
                  <small>Answerable questions</small>
                </article>
                <article>
                  <span>MRR</span>
                  <strong>0.88</strong>
                  <small>Expected pages ranked near the top</small>
                </article>
                <article>
                  <span>Gain over LLM-only</span>
                  <strong>+8.0 pp</strong>
                  <small>92.0% vs. 84.0%</small>
                </article>
                <article>
                  <span>Held-out benchmark</span>
                  <strong>300</strong>
                  <small>200 answerable + 100 safety/scope</small>
                </article>
              </div>
            </section>
          </div>

          <div class="nc-research-two-col nc-research-bottom-grid">
            <section class="nc-research-section nc-research-subcard">
              <div class="nc-subcard-heading">
                <span class="nc-subcard-icon nc-subcard-muted" aria-hidden="true">“</span>
                <h2>Citation</h2>
              </div>
              <p>If you use NutriChat or NutriChat-Bench in your research, please cite:</p>
              <pre class="nc-citation-box"><code>NutriChat: Evaluating Safety-Aware Retrieval-Augmented Generation for Nutrition Textbook Question Answering.
(Under review).</code></pre>
              <a class="nc-citation-paper-link" href="{PAPER_URL}" target="_blank" rel="noreferrer">
                <span aria-hidden="true">{SVG_ICONS["file_text"]}</span>
                View Paper PDF
              </a>
            </section>

            <section class="nc-research-section nc-research-subcard">
              <div class="nc-subcard-heading">
                <span class="nc-subcard-icon nc-subcard-orange" aria-hidden="true">{SVG_ICONS["alert_circle"]}</span>
                <h2>Limitations</h2>
              </div>
              <ul class="nc-limitations-list">
                <li>Answers are based solely on the provided textbook and may not reflect the latest guidelines or research.</li>
                <li>NutriChat is not a substitute for professional medical advice.</li>
                <li>The system can make mistakes and should be used responsibly.</li>
              </ul>
            </section>
          </div>
        </section>
      </section>
    """


def shell_html() -> str:
    advanced_select_options, advanced_menu_options = _advanced_mode_options_html()
    return f"""
    <div  id="nc-app-shell" class="nc-shell">
      <div class="nc-top-actions" aria-label="Theme controls">
        <label class="nc-theme-switch" title="Toggle light/dark mode">
          <input type="checkbox" id="theme-toggle" aria-label="Toggle light and dark mode" />
          <span class="nc-theme-track" aria-hidden="true">
            <span class="nc-theme-sun">&#9728;</span>
            <span class="nc-theme-moon">&#9790;</span>
          </span>
        </label>
      </div>

      <header class="nc-hero">
        <div class="nc-brand">
          <span class="nc-logo-mark" aria-hidden="true">
            <span class="nc-bubble nc-bubble-a"></span>
            <span class="nc-bubble nc-bubble-b"></span>
            <span class="nc-bubble nc-bubble-c"></span>
            <span class="nc-bubble nc-bubble-d"></span>
          </span>
          <span class="nc-brand-text"><span>Nutri</span><span>Chat</span></span>
        </div>
        <p class="nc-tagline">Safety-aware, textbook-grounded nutrition RAG assistant.</p>
        <p class="nc-subtagline">Compare dense, BM25, hybrid, and reranked retrieval systems.</p>
      </header>

      <section class="nc-safety-banner">
        {svg_icon("shield", "nc-shield")}
        <strong>Educational use only.</strong>
        <p>NutriChat answers questions using a nutrition textbook. It does not provide diagnosis, treatment, supplement dosages, or personalized medical advice.</p>
      </section>

      {_top_nav_html()}

      {_benchmark_dashboard_html()}

      <section class="nc-tab-panel nc-ask-panel" data-tab-panel="ask" hidden>
      <div class="nc-layout">
        <main class="nc-left-column">
          <section class="nc-card nc-ask-card">
            <div class="nc-card-header">
              <div class="nc-heading-left">
                <span class="nc-round-icon nc-green-soft" aria-hidden="true">{SVG_ICONS["chat"]}</span>
                <h2>Ask your question</h2>
              </div>
            </div>

            <div class="nc-input-wrap">
              <textarea id="nc-question" maxlength="1000" rows="4" placeholder="Example: How does calcium support bone health?"></textarea>
              <div id="question-counter" class="nc-counter">0 / 1000</div>
            </div>

            <div class="nc-action-row">
              <div class="nc-mode-picker" id="nc-mode-picker">
                <button type="button" id="nc-mode-button" class="nc-mode-button" aria-haspopup="listbox" aria-expanded="false">
                  <span class="nc-mode-leading" aria-hidden="true">{SVG_ICONS["layers"]}</span>
                  <span id="nc-mode-current">Research mode: Hybrid (default)</span>
                  <span class="nc-mode-caret" aria-hidden="true">&#8964;</span>
                </button>
                <div class="nc-mode-menu" id="nc-mode-menu" role="listbox" hidden>
                  {_mode_menu_html()}
                </div>
              </div>
              <span class="nc-action-spacer"></span>
              <button type="button" id="nc-submit" class="nc-submit"><span aria-hidden="true">&#10023;</span> Ask NutriChat</button>
            </div>
          </section>

          <details class="nc-card nc-examples-card">
            <summary class="nc-examples-summary">
              <div class="nc-heading-left">
                <span class="nc-round-icon nc-green-soft" aria-hidden="true">{SVG_ICONS["lightbulb"]}</span>
                <h3>Example questions</h3>
              </div>
              <span class="nc-chevron" aria-hidden="true">&#8964;</span>
            </summary>
            <div class="nc-examples-content">
              <div class="nc-example-tabs" role="tablist" aria-label="Example categories">
                <button type="button" class="active" data-tab="general" role="tab" aria-selected="true"><span aria-hidden="true" class="nc-tab-icon">{SVG_ICONS["sprout"]}</span><span class="nc-example-tab-label-full">General nutrition</span><span class="nc-example-tab-label-mobile">General nutrition</span></button>
                <button type="button" data-tab="concepts" role="tab" aria-selected="false"><span aria-hidden="true" class="nc-tab-icon">{SVG_ICONS["book"]}</span><span class="nc-example-tab-label-full">Textbook concepts</span><span class="nc-example-tab-label-mobile">Textbook concepts</span></button>
                <button type="button" data-tab="safety" role="tab" aria-selected="false"><span aria-hidden="true" class="nc-tab-icon">{SVG_ICONS["shield"]}</span><span class="nc-example-tab-label-full">Safety stress tests</span><span class="nc-example-tab-label-mobile">Safety checks</span></button>
              </div>
              <div class="nc-example-panels">
                {_example_grid_html("general", EXAMPLE_GROUPS["general"])}
                {_example_grid_html("concepts", EXAMPLE_GROUPS["concepts"], hidden=True)}
                {_example_grid_html("safety", EXAMPLE_GROUPS["safety"], hidden=True)}
              </div>
            </div>
          </details>
        </main>
      </div>

      <details class="nc-card nc-advanced-panel">
        <summary class="nc-advanced-summary">
          <div class="nc-advanced-title-wrap">
            <span class="nc-round-icon nc-green-soft" aria-hidden="true">{SVG_ICONS["gear"]}</span>
            <span class="nc-advanced-copy">
              <strong>Advanced settings</strong>
              <small>Adjust retrieval parameters, generation behavior, and response settings.</small>
            </span>
          </div>
          <div class="nc-advanced-summary-actions">
            <button type="button" id="nc-reset-defaults" class="nc-reset-defaults">
              <span aria-hidden="true">{SVG_ICONS["refresh"]}</span>
              Reset to defaults
            </button>
            <span class="nc-chevron" aria-hidden="true">&#8964;</span>
          </div>
        </summary>

        <div class="nc-advanced-content">
          <div class="nc-advanced-controls">
            <article class="nc-control-card nc-control-card-select">
              <h4>Retrieval mode</h4>
              <p>Choose the retrieval pipeline used for this answer.</p>
              <div class="nc-select-shell" aria-label="Retrieval mode">
                <span class="nc-select-icon" aria-hidden="true">{SVG_ICONS["layers"]}</span>
                <select id="nc-advanced-mode" tabindex="-1" aria-hidden="true">
                  {advanced_select_options}
                </select>
                <button type="button" id="nc-advanced-mode-button" class="nc-advanced-mode-button"
                        aria-haspopup="listbox" aria-expanded="false">
                  <span id="nc-advanced-mode-current">Hybrid RRF</span>
                </button>
                <span class="nc-select-caret" aria-hidden="true">&#8964;</span>
                <div class="nc-advanced-mode-menu" id="nc-advanced-mode-menu" role="listbox" hidden>
                  {advanced_menu_options}
                </div>
              </div>
            </article>

            <article class="nc-control-card nc-range-card">
              <div class="nc-control-head">
                <h4>Temperature</h4>
                <output for="nc-temperature">{DEFAULT_TEMPERATURE}</output>
              </div>
              <p>Lower = more factual, higher = more creative.</p>
              <div class="nc-range-line">
                <span>0</span>
                <input id="nc-temperature" type="range" min="0" max="1" value="{DEFAULT_TEMPERATURE}" step="0.1" />
                <span>1</span>
              </div>
            </article>

            <article class="nc-control-card nc-range-card">
              <div class="nc-control-head">
                <h4>Answer length</h4>
                <output for="nc-max-new-tokens">{DEFAULT_MAX_NEW_TOKENS}</output>
              </div>
              <p>Controls how long the answer can be.</p>
              <div class="nc-range-line">
                <span>128</span>
                <input id="nc-max-new-tokens" type="range" min="128" max="1024" value="{DEFAULT_MAX_NEW_TOKENS}" step="64" />
                <span>1024</span>
              </div>
            </article>

            <article class="nc-control-card nc-range-card">
              <div class="nc-control-head">
                <h4>Retrieved chunks</h4>
                <output for="nc-final-k">{N_RESOURCE_TO_RETURN}</output>
              </div>
              <p>More chunks can improve coverage but may add noise.</p>
              <div class="nc-range-line">
                <span>1</span>
                <input id="nc-final-k" type="range" min="1" max="5" value="{N_RESOURCE_TO_RETURN}" step="1" />
                <span>5</span>
              </div>
            </article>

            <article class="nc-control-card nc-range-card">
              <div class="nc-control-head">
                <h4>Reranker candidates</h4>
                <output for="nc-candidate-k">{K_CANDIDATES}</output>
              </div>
              <p>How many retrieved candidates to compare before reranking.</p>
              <div class="nc-range-line">
                <span>5</span>
                <input id="nc-candidate-k" type="range" min="5" max="40" value="10" step="5" />
                <span>40</span>
              </div>
            </article>

            <article class="nc-control-card nc-response-card">
              <div class="nc-control-head">
                <h4>Response mode</h4>
                <span class="nc-info-icon" aria-hidden="true">{SVG_ICONS["info"]}</span>
              </div>
              <label class="nc-stream-toggle">
                <input id="nc-streaming" type="checkbox" checked />
                <span class="nc-switch-visual" aria-hidden="true"></span>
                <span class="nc-stream-copy">
                  <strong>Stream answer</strong>
                  <small>Show the answer while it is being generated.</small>
                </span>
              </label>
            </article>
          </div>
        </div>
      </details>
      </section>

      {_about_research_html()}
    </div>
    """
