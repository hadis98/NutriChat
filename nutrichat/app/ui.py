import os
from functools import lru_cache

import gradio as gr

from nutrichat.config import (
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_NEW_TOKENS,
    K_CANDIDATES,
    N_RESOURCE_TO_RETURN,
)
from nutrichat.app.asset_loader import (
    CUSTOM_CSS,
    CUSTOM_HEAD,
    SPINNER_HTML,
    spinner_html,
)
from nutrichat.app.options import DEFAULT_SYSTEM_CHOICE
from nutrichat.app.service import NutriChatAppService
from nutrichat.app.shell import shell_html


os.environ["TOKENIZERS_PARALLELISM"] = "false"


@lru_cache(maxsize=1)
def get_service() -> NutriChatAppService:
    return NutriChatAppService()


def ask_with_lazy_service(*args):
    # This passes the exact original app arguments to the existing backend service.
    yield from get_service().ask(*args)


def show_loading(system_choice: str):
    system_choice = system_choice or ""
    if "reranker" in system_choice.lower() and "no reranker" not in system_choice.lower():
        message = "loading reranker and ranking sources..."
    else:
        message = "retrieving sources and generating your answer..."

    return (
        gr.update(value=spinner_html(message), visible=True),
        gr.update(interactive=False),
    )


def hide_loading():
    return gr.update(visible=False), gr.update(interactive=True)


def _backend_controls():
    with gr.Group(elem_classes=["nc-backend"]):
        query = gr.Textbox(value="", label="backend query", elem_id="backend-query")
        system_choice = gr.Textbox(
            value=DEFAULT_SYSTEM_CHOICE,
            label="backend system",
            elem_id="backend-system-choice",
        )
        temperature = gr.Textbox(
            value=str(DEFAULT_TEMPERATURE),
            label="backend temperature",
            elem_id="backend-temperature",
        )
        max_new_tokens = gr.Textbox(
            value=str(DEFAULT_MAX_NEW_TOKENS),
            label="backend max tokens",
            elem_id="backend-max-new-tokens",
        )
        final_k = gr.Textbox(
            value=str(N_RESOURCE_TO_RETURN),
            label="backend final k",
            elem_id="backend-final-k",
        )
        candidate_k = gr.Textbox(
            value=str(K_CANDIDATES),
            label="backend candidate k",
            elem_id="backend-candidate-k",
        )
        use_streaming = gr.Checkbox(
            value=True,
            label="backend streaming",
            elem_id="backend-use-streaming",
        )
        submit_btn = gr.Button("Ask NutriChat", elem_id="backend-submit")

    return (
        query,
        system_choice,
        temperature,
        max_new_tokens,
        final_k,
        candidate_k,
        use_streaming,
        submit_btn,
    )


def _result_outputs():
    with gr.Row(equal_height=False, elem_classes=["results-layout", "nc-ask-results-panel"]):
        with gr.Column(scale=7, elem_classes=["main-results-column"]):
            with gr.Tabs(elem_classes=["result-tabs"]):
                with gr.Tab("\U0001f4ac Answer"):
                    answer = gr.Markdown(
                        value="",
                        show_label=False,
                        elem_id="answer-output",
                        elem_classes=["answer-card"],
                    )

                with gr.Tab("\U0001f4d6 Retrieved Sources"):
                    sources = gr.HTML(
                        value="",
                        label="Retrieved sources",
                        elem_id="sources-output",
                    )

                with gr.Tab("\u2699\ufe0f Diagnostics"):
                    diagnostics = gr.HTML(
                        value="",
                        elem_id="diagnostics-output",
                    )

        with gr.Column(scale=3, min_width=300, elem_classes=["side-info-column"]):
            quick_info = gr.HTML(
                value="",
                label="Quick Info",
                elem_id="quick-info-output",
            )

            about_answer = gr.HTML(
                value="",
                label="About this answer",
                elem_id="about-answer-output",
            )

    return answer, sources, diagnostics, quick_info, about_answer


def _wire_submit(
    submit_btn,
    loading,
    inputs,
    outputs,
):
    submit_btn.click(
        fn=show_loading,
        inputs=inputs["system_choice"],
        outputs=[loading, submit_btn],
        queue=False,
    ).then(
        fn=ask_with_lazy_service,
        inputs=[
            inputs["query"],
            inputs["system_choice"],
            inputs["temperature"],
            inputs["max_new_tokens"],
            inputs["final_k"],
            inputs["candidate_k"],
            inputs["use_streaming"],
        ],
        outputs=outputs,
    ).then(
        fn=hide_loading,
        inputs=None,
        outputs=[loading, submit_btn],
        queue=False,
    )


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="NutriChat RAG", elem_id="nutrichat-app") as demo:
        with gr.Column(elem_id="main-container"):
            gr.HTML(shell_html())

            (
                query,
                system_choice,
                temperature,
                max_new_tokens,
                final_k,
                candidate_k,
                use_streaming,
                submit_btn,
            ) = _backend_controls()

            loading = gr.HTML(
                SPINNER_HTML,
                visible=False,
                elem_classes=["nc-ask-results-panel", "nc-ask-loading-panel"],
            )
            outputs = _result_outputs()

            _wire_submit(
                submit_btn=submit_btn,
                loading=loading,
                inputs={
                    "query": query,
                    "system_choice": system_choice,
                    "temperature": temperature,
                    "max_new_tokens": max_new_tokens,
                    "final_k": final_k,
                    "candidate_k": candidate_k,
                    "use_streaming": use_streaming,
                },
                outputs=outputs,
            )

    return demo
